# app/services/scene_segment_ai_service.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, not_, exists
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging
import traceback
import json

from app.models.script import Script, ScriptCreationMethod
from app.models.beats import Beat, MasterBeatSheet, ActEnum
from app.models.scenes import SceneDescription
from app.models.scene_segments import SceneSegment, SceneSegmentComponent, ComponentType
from app.schemas.scene_segment_ai import (GeneratedSceneSegment, SceneSegmentGenerationResponse, 
                                      AISceneComponent, AISceneSegmentGenerationResponse,
                                      AISceneComponentResponse, GeneratedSceneSegmentResponseResponse)


from app.services.openai_service import AzureOpenAIService
from app.services.scene_segment_service import SceneSegmentService

logger = logging.getLogger(__name__)

class SceneSegmentAIService:
    def __init__(self):
        self.openai_service = AzureOpenAIService()
    
    def format_scene_components_to_fountain(self, components: List[AISceneComponent]) -> str:
        """
        Format scene components as fountain text for display.
        """
        fountain_text = ""
        for comp in components:
            if comp.component_type == ComponentType.HEADING:
                fountain_text += f"{comp.content}\n\n"
            elif comp.component_type == ComponentType.ACTION:
                fountain_text += f"{comp.content}\n\n"
            elif comp.component_type == ComponentType.DIALOGUE:
                fountain_text += f"{comp.character_name}\n"
                if comp.parenthetical:
                    fountain_text += f"({comp.parenthetical})\n"
                fountain_text += f"{comp.content}\n\n"
            elif comp.component_type == ComponentType.TRANSITION:
                fountain_text += f"{comp.content}\n\n"
        return fountain_text
    
    def find_next_scene_without_segment(self, db: Session, script_id: UUID) -> Optional[SceneDescription]:
        """
        Find the next scene description that doesn't have a segment generated yet.
        Processes beats in order of position, then scenes within each beat by position.
        """
        # Subquery to find scene descriptions that already have segments
        scene_descriptions_with_segments = (
            db.query(SceneSegment.scene_description_id)
            .filter(
                SceneSegment.script_id == script_id,
                SceneSegment.is_deleted.is_(False)
            )
            .subquery()
        )
        
        # Find scene descriptions without segments, ordered by beat position then scene position
        next_scene = (
            db.query(SceneDescription)
            .join(Beat, SceneDescription.beat_id == Beat.id)
            .filter(
                Beat.script_id == script_id,
                SceneDescription.is_deleted.is_(False),
                not_(SceneDescription.id.in_(scene_descriptions_with_segments))
            )
            .order_by(Beat.position, SceneDescription.position)
            .first()
        )
        
        return next_scene
        
    async def generate_next_segment(
        self,
        db: Session,
        script_id: UUID,
        user_id: UUID
    ) -> AISceneSegmentGenerationResponse:
        """
        Generate a scene segment for the next available scene without a segment.
        """
        # Verify script exists and user has access
        script = db.query(Script).filter(
            Script.id == script_id,
            Script.user_id == user_id
        ).first()
        
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found or unauthorized access"
            )
        
        # Verify script was created with AI
        if script.creation_method != ScriptCreationMethod.WITH_AI:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only scripts created with AI support scene generation"
            )
        
        # Find the next scene without a segment
        next_scene = self.find_next_scene_without_segment(db, script_id)
        
        if not next_scene:
            return AISceneSegmentGenerationResponse(
                success=False,
                creation_method=script.creation_method.value,
                message="All scenes already have segments generated"
            )

        
        # Get beat information
        beat = db.query(Beat).filter(Beat.id == next_scene.beat_id).first()
        if not beat:
            return AISceneSegmentGenerationResponse(
                success=False,
                input_context={
                    "script_id": str(script_id),
                    "scene_description_id": str(next_scene.id)
                },
                creation_method=script.creation_method.value,
                message="Beat not found for scene",
                error="Beat not found"
            )
        
        # Get master beat sheet for template information
        master_beat_sheet = db.query(MasterBeatSheet).filter(
            MasterBeatSheet.id == beat.master_beat_sheet_id
        ).first()
        
        if not master_beat_sheet:
            return AISceneSegmentGenerationResponse(
                success=False,
                input_context={
                    "script_id": str(script_id),
                    "scene_description_id": str(next_scene.id),
                    "beat_id": str(beat.id),
                    "beat_title": beat.beat_title
                },
                creation_method=script.creation_method.value,
                message="Master beat sheet not found",
                error="Master beat sheet not found"
            )

        
        # Parse template data to get original beat definition
        template_data = master_beat_sheet.template
        if isinstance(template_data, str):
            template_data = json.loads(template_data)
        
        beat_template = next(
            (b for b in template_data.get("beats", []) if b.get("position") == beat.position),
            None
        )
        
        min_word_count = 800  # Default value if not found
        if beat_template and "word_count_maximum" in beat_template:
            min_word_count = beat_template["word_count_maximum"]

        # Get previous scenes for context
        previous_scenes = [
            scene.scene_heading 
            for scene in db.query(SceneDescription)
            .join(Beat)
            .filter(
                Beat.script_id == script.id,
                or_(
                    and_(Beat.position < beat.position),
                    and_(
                        Beat.position == beat.position,
                        SceneDescription.position < next_scene.position
                    )
                )
            )
            .order_by(Beat.position, SceneDescription.position)
            .all()
        ]
        input_context = {
            "script_id": str(script_id),
            "script_title": script.title,
            "genre": script.genre,
            "beat_id": str(beat.id),
            "beat_title": beat.beat_title,
            "beat_position": beat.position,
            "scene_description_id": str(next_scene.id),
            "scene_title": next_scene.scene_heading,
            "scene_description": next_scene.scene_description,
            "scene_position": next_scene.position,
            "min_word_count": min_word_count,
            "previous_scenes": previous_scenes
        }

        # Generate scene segment using OpenAI
        try:
            generated_segment = self.openai_service.generate_scene_segment(
                story_synopsis=script.story,
                genre=script.genre,
                arc_structure=master_beat_sheet.beat_sheet_type.value,
                beat_position=beat.position,
                scene_position=next_scene.position,
                template_beat_title=beat_template.get("name", "") if beat_template else "",
                template_beat_definition=beat_template.get("description", "") if beat_template else "",
                story_specific_beat_title=beat.beat_title,
                story_specific_beat_description=beat.beat_description,
                scene_title=next_scene.scene_heading,
                scene_description=next_scene.scene_description,
                min_word_count=min_word_count,
                previous_scenes=previous_scenes
            )
            
            # Get the next available segment number
            next_segment_number = SceneSegmentService.fetch_next_segment_number(db, script_id)
            if next_segment_number is None:
                next_segment_number = 1000.0
            else:
                next_segment_number += 1000.0
            
            # Create components for creation
            import uuid
            from schemas.scene_segment import ComponentCreate
            component_models = []
            for comp in generated_segment.components:
                component_data = {
                    "component_type": comp.component_type,
                    "position": comp.position,
                    "content": comp.content,
                    "id": uuid.uuid4()  # Generate a UUID for each component
                }
                
                # Add dialogue-specific fields if applicable
                if comp.component_type == ComponentType.DIALOGUE:
                    component_data["character_name"] = comp.character_name
                    component_data["parenthetical"] = comp.parenthetical
                
                component_create = ComponentCreate(**component_data)
                component_models.append(component_create)
            
            # Create segment
            from schemas.scene_segment import SceneSegmentCreate
            segment_create = SceneSegmentCreate(
                script_id=script.id,
                beat_id=beat.id,
                scene_description_id=next_scene.id,
                segment_number=next_segment_number,
                components=component_models
            )
            
            # Use existing service to create the segment
            created_segment = SceneSegmentService.create_scene_segment(db, segment_create)
            
            # Query the database for the components of the created segment
            components = db.query(SceneSegmentComponent).filter(
                SceneSegmentComponent.scene_segment_id == created_segment.id,
                SceneSegmentComponent.is_deleted.is_(False)
            ).order_by(SceneSegmentComponent.position).all()
            
            # Create AISceneComponentResponse objects using database component IDs
            ai_components = []
            for comp in components:
                ai_component = AISceneComponentResponse(
                    component_type=comp.component_type,
                    position=comp.position,
                    content=comp.content,
                    character_name=comp.character_name,
                    parenthetical=comp.parenthetical,
                    component_id=comp.id
                )
                ai_components.append(ai_component)
            
            # Format fountain text using the AI components
            fountain_text = self.format_scene_components_to_fountain(generated_segment.components)
            
            # Return AISceneSegmentGenerationResponse with properly structured components
            return AISceneSegmentGenerationResponse(
                success=True,
                input_context=input_context,
                generated_segment=GeneratedSceneSegmentResponseResponse(components=ai_components),
                fountain_text=fountain_text,
                scene_segment_id=created_segment.id,
                creation_method=script.creation_method.value,
                message="Successfully generated scene segment"
            )
                
        except Exception as e:
            logger.error(f"Failed to generate scene segment: {str(e)}")
            logger.error(traceback.format_exc())
            return AISceneSegmentGenerationResponse(
                success=False,
                input_context=input_context,
                creation_method=script.creation_method.value,
                message="Failed to generate scene segment",
                error=str(e)
            )

    async def get_or_generate_first_segment(
        self,
        db: Session,
        script_id: UUID,
        user_id: UUID
    ) -> AISceneSegmentGenerationResponse:
        """
        Get the first scene segment for a script or generate it if it doesn't exist.
        
        Args:
            db: Database session
            script_id: UUID of the script
            user_id: UUID of the requesting user
            
        Returns:
            SceneSegmentGenerationResponse with either existing or generated segment
        """
        # Verify script exists and user has access
        script = db.query(Script).filter(
            Script.id == script_id,
            Script.user_id == user_id
        ).first()
        
        if not script:
            return SceneSegmentGenerationResponse(
                success=False,
                creation_method="UNKNOWN",
                message="Script not found or unauthorized access",
                error="Script not found"
            )
        
        # Check if script has any existing scene segments
        existing_segment = db.query(SceneSegment).filter(
            SceneSegment.script_id == script_id,
            SceneSegment.is_deleted.is_(False)
        ).order_by(SceneSegment.segment_number).first()
        
        if existing_segment:
            # Return existing first segment
            components = db.query(SceneSegmentComponent).filter(
                SceneSegmentComponent.scene_segment_id == existing_segment.id,
                SceneSegmentComponent.is_deleted.is_(False)
            ).order_by(SceneSegmentComponent.position).all()
            
            # Convert to AISceneComponent format for response
            ai_components = []
            for comp in components:
                ai_component = AISceneComponentResponse(
                    component_type=comp.component_type,
                    position=comp.position,
                    content=comp.content,
                    character_name=comp.character_name,
                    parenthetical=comp.parenthetical,
                    component_id=comp.id
                )
                ai_components.append(ai_component)
            
            # Format fountain text for display
            fountain_text = self.format_scene_components_to_fountain(ai_components)
            
            return AISceneSegmentGenerationResponse(
                success=True,
                input_context={
                    "script_id": str(script.id),
                    "script_title": script.title,
                    "source": "existing"
                },
                generated_segment=GeneratedSceneSegmentResponseResponse(components=ai_components),
                fountain_text=fountain_text,
                scene_segment_id=existing_segment.id,
                creation_method=script.creation_method.value,
                message="Found existing first scene segment"
            )
        else:
            # No existing segment, generate a new one
            return await self.generate_next_segment(
                db=db,
                script_id=script_id,
                user_id=user_id
            )
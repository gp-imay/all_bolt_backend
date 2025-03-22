# app/services/scene_segment_ai_service.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, not_, exists
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging
import traceback
import json
import math

from app.models.script import Script, ScriptCreationMethod
from app.models.beats import Beat, MasterBeatSheet, ActEnum
from app.models.scenes import SceneDescription
from app.models.scene_segments import SceneSegment, SceneSegmentComponent, ComponentType
from app.schemas.scene_segment_ai import (GeneratedSceneSegment, SceneSegmentGenerationResponse, 
                                      AISceneComponent, AISceneSegmentGenerationResponse,
                                      AISceneComponentResponse, GeneratedSceneSegmentResponseResponse)


from app.services.openai_service import AzureOpenAIService
from app.services.scene_segment_service import SceneSegmentService
from app.services.scene_description_service import SceneDescriptionService

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
    
    async def ensure_scene_descriptions_exist(self, db, script_id, user_id):
        """
        Ensures scene descriptions exist for the script by checking each beat in order.
        If a beat without scene descriptions is found, generates descriptions for that beat.
        
        Args:
            db: Database session
            script_id: UUID of the script
            user_id: UUID of the requesting user
            
        Returns:
            tuple: (found_or_created_descriptions, new_description_generated, error_message or None)
        """
        # Get all beats for this script in position order
        beats = db.query(Beat).filter(
            Beat.script_id == script_id,
            Beat.is_deleted.is_(False)
        ).order_by(Beat.position).all()
        
        if not beats:
            return False, False, "No beats found for this script"
        
        # Check each beat in order
        for beat in beats:
            # Check if this beat has any scene descriptions
            has_descriptions = db.query(exists().where(
                and_(
                    SceneDescription.beat_id == beat.id,
                    SceneDescription.is_deleted.is_(False)
                )
            )).scalar()
            
            if not has_descriptions:
                # Found a beat without scene descriptions - generate them
                scene_description_service = SceneDescriptionService()
                try:
                    result = await scene_description_service.generate_scene_description_for_beat(
                        db=db,
                        beat_id=beat.id,
                        user_id=user_id
                    )
                    return True, True, None  # Successfully generated new scene descriptions
                except Exception as e:
                    error_message = f"Failed to generate scene descriptions for beat {beat.id}: {str(e)}"
                    logger.error(error_message)
                    logger.error(traceback.format_exc())
                    return False, False, error_message
        
        # If we get here, all beats already have scene descriptions
        return True, False, None
    
    def find_next_scene_without_segment(self, db: Session, script_id: UUID) -> Tuple[Optional[SceneDescription], bool]:
        """
        Find the next scene description that doesn't have a segment generated yet.
        Processes beats in order of position, then scenes within each beat by position.
        
        Returns:
            Tuple containing:
            - The next scene description without a segment (or None if not found)
            - A boolean indicating whether any scene descriptions exist for this script
        """
        # First check if any scene descriptions exist for this script
        scene_descriptions_exist = db.query(exists().where(
            SceneDescription.beat_id.in_(
                db.query(Beat.id).filter(Beat.script_id == script_id)
            )
        )).scalar()
        # If no scene descriptions exist at all, return None and False
        if not scene_descriptions_exist:
            return None, False
        
        # Subquery to find scene descriptions that already have segments
        # scene_descriptions_with_segments = (
        #     db.query(SceneSegment.scene_description_id)
        #     .filter(
        #         SceneSegment.script_id == script_id,
        #         SceneSegment.is_deleted.is_(False)
        #     )
        #     .scalar_subquery()  # Fixed the SQLAlchemy warning
        # )
        
        # Find scene descriptions without segments, ordered by beat position then scene position
        next_scene = (
            db.query(SceneDescription)
            .join(Beat, SceneDescription.beat_id == Beat.id)
            .outerjoin(
                SceneSegment, 
                and_(
                    SceneSegment.scene_description_id == SceneDescription.id,
                    SceneSegment.is_deleted.is_(False)
                )
            )
            .filter(
                Beat.script_id == script_id,
                SceneDescription.is_deleted.is_(False),
                SceneSegment.id.is_(None)  # Only include scenes with no segments
            )
            .order_by(Beat.position, SceneDescription.position)
            .first()
        )
        
        # Return the next scene and True (indicating scenes exist)
        return next_scene, True
        
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
        
        descriptions_exist, newly_generated, error = await self.ensure_scene_descriptions_exist(db, script_id, user_id)
        if error:
            return AISceneSegmentGenerationResponse(
                success=False,
                creation_method=script.creation_method.value,
                message=error
            )
        # Find the next scene without a segment
        next_scene, scenes_exist = self.find_next_scene_without_segment(db, script_id)
        # Handle different cases
        if not scenes_exist:
            return AISceneSegmentGenerationResponse(
                success=False,
                creation_method=script.creation_method.value,
                message="No scene descriptions found for this script. Please generate scene descriptions first.",
                error="No scene descriptions exist"
            )
        
        if not next_scene:
            return AISceneSegmentGenerationResponse(
                success=False,
                creation_method=script.creation_method.value,
                message="All scenes already have segments generated",
                error="All scenes have segments"
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
        if beat_template and "word_count_maximum" in beat_template and "number_of_scenes" in beat_template:
            min_word_count = math.ceil(beat_template["word_count_maximum"]/ beat_template["number_of_scenes"])
        
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
            from app.schemas.scene_segment import ComponentCreate
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
            from app.schemas.scene_segment import SceneSegmentCreate
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
            return AISceneSegmentGenerationResponse(
                success=False,
                creation_method="UNKNOWN",
                message="Script not found or unauthorized access",
                error="Script not found"
            )
        
        # Ensure scene descriptions exist
        descriptions_exist, newly_generated, error = await self.ensure_scene_descriptions_exist(db, script_id, user_id)

        if error:
            return AISceneSegmentGenerationResponse(
                success=False,
                creation_method=script.creation_method.value,
                message=error
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
            # Check if any scene descriptions exist before trying to generate
            scene_desc_exists = db.query(exists().where(
                SceneDescription.beat_id.in_(
                    db.query(Beat.id).filter(Beat.script_id == script_id)
                )
            )).scalar()
            
            if not scene_desc_exists:
                # No scene descriptions exist yet - let's generate them first
                
                try:
                    # Find beats for this script that need scene descriptions
                    beats = db.query(Beat).filter(
                        Beat.script_id == script_id,
                        or_(Beat.is_deleted.is_(False), Beat.is_deleted.is_(None))
                    ).order_by(Beat.position).all()
                    
                    if not beats:
                        return AISceneSegmentGenerationResponse(
                            success=False,
                            input_context={
                                "script_id": str(script.id),
                                "script_title": script.title
                            },
                            creation_method=script.creation_method.value,
                            message="No beats found for this script. Please create beats first.",
                            error="No beats exist"
                        )
                    
                    # Generate scene descriptions for the first beat
                    scene_description_service = SceneDescriptionService()
                    generation_result = await scene_description_service.generate_scene_description_for_beat(
                        db=db,
                        beat_id=beats[0].id,
                        user_id=user_id
                    )
                    
                    # Log the result of scene description generation
                    logger.info(f"Generated scene descriptions for beat {beats[0].id}")
                    
                    # Now we should have scene descriptions, so continue with segment generation
                except Exception as e:
                    logger.error(f"Failed to generate scene descriptions: {str(e)}")
                    return AISceneSegmentGenerationResponse(
                        success=False,
                        input_context={
                            "script_id": str(script.id),
                            "script_title": script.title
                        },
                        creation_method=script.creation_method.value,
                        message=f"Failed to automatically generate scene descriptions: {str(e)}",
                        error="Scene description generation failed"
                    )
                
            # No existing segment, generate a new one
            return await self.generate_next_segment(
                db=db,
                script_id=script_id,
                user_id=user_id
            )
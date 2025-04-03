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
from app.models.scene_segments import (SceneSegment, SceneSegmentComponent, ComponentType, 
                                       ShorteningAlternative, ShorteningSelectionHistory,
                                       RewriteAlternative, RewriteSelectionHistory,
                                       ExpansionAlternative, ExpansionSelectionHistory,
                                       ContinuationAlternative, ContinuationSelectionHistory)
from app.schemas.scene_segment_ai import (GeneratedSceneSegment, SceneSegmentGenerationResponse, 
                                      AISceneComponent, AISceneSegmentGenerationResponse,
                                      AISceneComponentResponse, GeneratedSceneSegmentResponseResponse,
                                      ShorteningAlternativeType, ShortenComponentResponse, ScriptRewrite,ScriptShorten,
                                      RewriteComponentResponse, RewriteAlternativeType,
                                      ExpandComponentResponse, ExpansionAlternativeType, ScriptExpansion,
                                      ContinueComponentResponse, ContinuationAlternativeType,ScriptContinuation)
from app.schemas.scene_segment import ComponentUpdate


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
        
    @staticmethod
    def shorten_component(db: Session, component_id: UUID) -> Dict[str, Any]:
        """
        Shorten a component's content using AI while maintaining its meaning.
        Returns multiple alternative shortened versions.
        """
        # Get the component with validation
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Only allow shortening for supported component types
        if component.component_type not in [ComponentType.ACTION, ComponentType.DIALOGUE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot shorten component of type {component.component_type}"
            )
        
        # Get segment for context
        segment = db.query(SceneSegment).filter(
            SceneSegment.id == component.scene_segment_id
        ).first()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent segment not found"
            )
        
        # Get script for genre information
        script = db.query(Script).filter(Script.id == segment.script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Initialize OpenAI service
        openai_service = AzureOpenAIService()
        
        # Process based on component type
        try:
            if component.component_type == ComponentType.ACTION:
                alternatives = openai_service.shorten_action_component(
                    text=component.content,
                    context={
                        "genre": script.genre,
                        "script_title": script.title
                    }
                )
            elif component.component_type == ComponentType.DIALOGUE:
                alternatives = openai_service.shorten_dialogue_component(
                    text=component.content,
                    character_name=component.character_name,
                    context={
                        "genre": script.genre,
                        "script_title": script.title,
                        "parenthetical": component.parenthetical
                    }
                )
            
            # Delete any existing alternatives
            db.query(ShorteningAlternative).filter(
                ShorteningAlternative.component_id == component_id
            ).delete(synchronize_session=False)
            
            # Store themed alternatives in database
            db_alternatives = []
            
            # Concise alternative
            concise = ShorteningAlternative(
                component_id=component_id,
                alternative_type=ShorteningAlternativeType.CONCISE,
                shortened_text=alternatives.concise.shortened_text,
                explanation=alternatives.concise.explanation
            )
            db.add(concise)
            db_alternatives.append((ShorteningAlternativeType.CONCISE, concise))
            
            # Dramatic alternative
            dramatic = ShorteningAlternative(
                component_id=component_id,
                alternative_type=ShorteningAlternativeType.DRAMATIC,
                shortened_text=alternatives.dramatic.shortened_text,
                explanation=alternatives.dramatic.explanation
            )
            db.add(dramatic)
            db_alternatives.append((ShorteningAlternativeType.DRAMATIC, dramatic))
            
            # Minimal alternative
            minimal = ShorteningAlternative(
                component_id=component_id,
                alternative_type=ShorteningAlternativeType.MINIMAL,
                shortened_text=alternatives.minimal.shortened_text,
                explanation=alternatives.minimal.explanation
            )
            db.add(minimal)
            db_alternatives.append((ShorteningAlternativeType.MINIMAL, minimal))
            
            # Poetic alternative
            poetic = ShorteningAlternative(
                component_id=component_id,
                alternative_type=ShorteningAlternativeType.POETIC,
                shortened_text=alternatives.poetic.shortened_text,
                explanation=alternatives.poetic.explanation
            )
            db.add(poetic)
            db_alternatives.append((ShorteningAlternativeType.POETIC, poetic))
            
            # Punchy alternative
            humorous = ShorteningAlternative(
                component_id=component_id,
                alternative_type=ShorteningAlternativeType.HUMOROUS,
                shortened_text=alternatives.humorous.shortened_text,
                explanation=alternatives.humorous.explanation
            )
            db.add(humorous)
            db_alternatives.append((ShorteningAlternativeType.HUMOROUS, humorous))
            
            db.commit()
            
            # Create response object
            return ShortenComponentResponse(
                component_id=component_id,
                original_text=component.content,
                concise=ScriptShorten(
                    shortened_text=alternatives.concise.shortened_text,
                    explanation=alternatives.concise.explanation
                ),
                dramatic=ScriptShorten(
                    shortened_text=alternatives.dramatic.shortened_text,
                    explanation=alternatives.dramatic.explanation
                ),
                minimal=ScriptShorten(
                    shortened_text=alternatives.minimal.shortened_text,
                    explanation=alternatives.minimal.explanation
                ),
                poetic=ScriptShorten(
                    shortened_text=alternatives.poetic.shortened_text,
                    explanation=alternatives.poetic.explanation
                ),
                humorous=ScriptShorten(
                    shortened_text=alternatives.humorous.shortened_text,
                    explanation=alternatives.humorous.explanation
                )
            )
            
        except Exception as e:
            db.rollback()
            logger.error(traceback.format_exc())
            logger.error(f"Error generating shortening alternatives: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating shortening alternatives: {str(e)}"
            )
    @staticmethod
    def update_component(
        db: Session, 
        component_id: UUID, 
        update_data: ComponentUpdate
    ) -> SceneSegmentComponent:
        """
        Update a component
        """
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
                
        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(component, key, value)
                
        try:
            db.commit()
            db.refresh(component)
            return component
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating component: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating component: {str(e)}"
            )

    @staticmethod
    def apply_shortening_alternative(
        db: Session, 
        component_id: UUID, 
        alternative_text: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a selected shortening alternative to a component and record the selection.
        Only updates if the content would change and only records selection if different from current.
        
        Args:
            db: Database session
            component_id: ID of the component to update
            alternative_type: Type of shortening alternative to apply
            user_id: ID of the user making the selection
            
        Returns:
            Dictionary with updated component and status information
            
        Raises:
            HTTPException: If component or alternative not found, or on database error
        """
        def _get_status_message(is_already_applied: bool, is_same_selection: bool) -> str:
            """Generate an appropriate status message based on what happened."""
            if is_already_applied and is_same_selection:
                return "This alternative is already applied and was previously selected."
            elif is_already_applied:
                return "This alternative was already applied, but your selection has been recorded."
            elif is_same_selection:
                return "Component content updated, but this selection type was already recorded."
            else:
                return "Alternative successfully applied and recorded."
        # Find the component
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Get the specific alternative
        alternative = db.query(ShorteningAlternative).filter(
            and_(
                ShorteningAlternative.component_id == component_id,
                ShorteningAlternative.shortened_text == alternative_text,
                ShorteningAlternative.is_deleted.is_(False)
            )
        ).first()
        
        if not alternative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alternative of type {alternative_text} not found"
            )
        
        try:
            # Check if the component already has this alternative's content
            is_already_applied = component.content == alternative.shortened_text
            
            # Get the most recent selection for this component (if any)
            latest_selection = db.query(ShorteningSelectionHistory).filter(
                ShorteningSelectionHistory.component_id == component_id
            ).order_by(
                ShorteningSelectionHistory.selected_at.desc()
            ).first()
            
            is_same_selection = False
            if latest_selection and latest_selection.alternative_type == alternative_text:
                is_same_selection = True
                
            # Only update and record if something would change
            if not is_already_applied:
                # Update the component with the selected alternative's text
                component.content = alternative.shortened_text
                component.updated_at = func.now()
            
            # Only add to history if this is a different selection than the most recent one
            if not is_same_selection:
                # Record this selection in the history table
                selection_history = ShorteningSelectionHistory(
                    user_id=user_id,
                    component_id=component_id,
                    alternative_id=alternative.id,
                    alternative_type=alternative.alternative_type
                )
                db.add(selection_history)
            
            db.commit()
            
            if not is_already_applied:
                db.refresh(component)
            
            return {
                "component": component,
                "was_updated": not is_already_applied,
                "was_recorded": not is_same_selection,
                "message": _get_status_message(is_already_applied, is_same_selection)
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying shortened text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying shortened text: {str(e)}"
            )

    @staticmethod
    def rewrite_component(db: Session, component_id: UUID) -> Dict[str, Any]:
        """
        Rewrite a component's content using AI while maintaining its meaning.
        Returns multiple alternative rewritten versions.
        """
        # Get the component with validation
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Only allow rewriting for supported component types
        if component.component_type not in [ComponentType.ACTION, ComponentType.DIALOGUE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot rewrite component of type {component.component_type}"
            )
        
        # Get segment for context
        segment = db.query(SceneSegment).filter(
            SceneSegment.id == component.scene_segment_id
        ).first()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent segment not found"
            )
        
        # Get script for genre information
        script = db.query(Script).filter(Script.id == segment.script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Get additional character context if available
        character_traits = ""
        if component.component_type == ComponentType.DIALOGUE and component.character_name:
            # Here you could potentially look up character information from a character database
            # For now, we'll leave it blank or could derive from previous dialogues
            pass
        
        # Initialize OpenAI service
        openai_service = AzureOpenAIService()
        
        # Process based on component type
        try:
            if component.component_type == ComponentType.ACTION:
                alternatives = openai_service.rewrite_action_component(
                    text=component.content,
                    context={
                        "genre": script.genre,
                        "script_title": script.title
                    }
                )
            elif component.component_type == ComponentType.DIALOGUE:
                alternatives = openai_service.rewrite_dialogue_component(
                    text=component.content,
                    character_name=component.character_name,
                    context={
                        "genre": script.genre,
                        "script_title": script.title,
                        "parenthetical": component.parenthetical,
                        "character_traits": character_traits
                    }
                )
            
            # Delete any existing alternatives
            db.query(RewriteAlternative).filter(
                RewriteAlternative.component_id == component_id
            ).delete(synchronize_session=False)
            
            # Store themed alternatives in database
            db_alternatives = []
            
            # Concise alternative
            concise = RewriteAlternative(
                component_id=component_id,
                alternative_type=RewriteAlternativeType.CONCISE,
                rewritten_text=alternatives.concise.rewritten_text,
                explanation=alternatives.concise.explanation
            )
            db.add(concise)
            db_alternatives.append((RewriteAlternativeType.CONCISE, concise))
            
            # Dramatic alternative
            dramatic = RewriteAlternative(
                component_id=component_id,
                alternative_type=RewriteAlternativeType.DRAMATIC,
                rewritten_text=alternatives.dramatic.rewritten_text,
                explanation=alternatives.dramatic.explanation
            )
            db.add(dramatic)
            db_alternatives.append((RewriteAlternativeType.DRAMATIC, dramatic))
            
            # Minimal alternative
            minimal = RewriteAlternative(
                component_id=component_id,
                alternative_type=RewriteAlternativeType.MINIMAL,
                rewritten_text=alternatives.minimal.rewritten_text,
                explanation=alternatives.minimal.explanation
            )
            db.add(minimal)
            db_alternatives.append((RewriteAlternativeType.MINIMAL, minimal))
            
            # Poetic alternative
            poetic = RewriteAlternative(
                component_id=component_id,
                alternative_type=RewriteAlternativeType.POETIC,
                rewritten_text=alternatives.poetic.rewritten_text,
                explanation=alternatives.poetic.explanation
            )
            db.add(poetic)
            db_alternatives.append((RewriteAlternativeType.POETIC, poetic))
            
            # Humorous alternative
            humorous = RewriteAlternative(
                component_id=component_id,
                alternative_type=RewriteAlternativeType.HUMOROUS,
                rewritten_text=alternatives.humorous.rewritten_text,
                explanation=alternatives.humorous.explanation
            )
            db.add(humorous)
            db_alternatives.append((RewriteAlternativeType.HUMOROUS, humorous))
            
            db.commit()
            
            # Create response object
            return RewriteComponentResponse(
                component_id=component_id,
                original_text=component.content,
                concise=ScriptRewrite(
                    rewritten_text=alternatives.concise.rewritten_text,
                    explanation=alternatives.concise.explanation
                ),
                dramatic=ScriptRewrite(
                    rewritten_text=alternatives.dramatic.rewritten_text,
                    explanation=alternatives.dramatic.explanation
                ),
                minimal=ScriptRewrite(
                    rewritten_text=alternatives.minimal.rewritten_text,
                    explanation=alternatives.minimal.explanation
                ),
                poetic=ScriptRewrite(
                    rewritten_text=alternatives.poetic.rewritten_text,
                    explanation=alternatives.poetic.explanation
                ),
                humorous=ScriptRewrite(
                    rewritten_text=alternatives.humorous.rewritten_text,
                    explanation=alternatives.humorous.explanation
                )
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating rewriting alternatives: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating rewriting alternatives: {str(e)}"
            )

    @staticmethod
    def apply_rewrite_alternative(
        db: Session, 
        component_id: UUID, 
        rewritten_text: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a selected rewrite alternative to a component and record the selection.
        Only updates if the content would change and only records selection if different from current.
        
        Args:
            db: Database session
            component_id: ID of the component to update
            rewritten_text: The selected rewritten text to apply
            user_id: ID of the user making the selection
            
        Returns:
            Dictionary with updated component and status information
            
        Raises:
            HTTPException: If component or alternative not found, or on database error
        """
        def _get_status_message(is_already_applied: bool, is_same_selection: bool) -> str:
            """Generate an appropriate status message based on what happened."""
            if is_already_applied and is_same_selection:
                return "This alternative is already applied and was previously selected."
            elif is_already_applied:
                return "This alternative was already applied, but your selection has been recorded."
            elif is_same_selection:
                return "Component content updated, but this selection type was already recorded."
            else:
                return "Alternative successfully applied and recorded."
            
        # Find the component
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Get the specific alternative
        alternative = db.query(RewriteAlternative).filter(
            and_(
                RewriteAlternative.component_id == component_id,
                RewriteAlternative.rewritten_text == rewritten_text,
                RewriteAlternative.is_deleted.is_(False)
            )
        ).first()
        
        if not alternative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alternative with provided rewritten text not found"
            )
        
        try:
            # Check if the component already has this alternative's content
            is_already_applied = component.content == alternative.rewritten_text
            
            # Get the most recent selection for this component (if any)
            latest_selection = db.query(RewriteSelectionHistory).filter(
                RewriteSelectionHistory.component_id == component_id
            ).order_by(
                RewriteSelectionHistory.selected_at.desc()
            ).first()
            
            is_same_selection = False
            if latest_selection and latest_selection.alternative_type == alternative.alternative_type:
                is_same_selection = True
                
            # Only update and record if something would change
            if not is_already_applied:
                # Update the component with the selected alternative's text
                component.content = alternative.rewritten_text
                component.updated_at = func.now()
            
            # Only add to history if this is a different selection than the most recent one
            if not is_same_selection:
                # Record this selection in the history table
                selection_history = RewriteSelectionHistory(
                    user_id=user_id,
                    component_id=component_id,
                    alternative_id=alternative.id,
                    alternative_type=alternative.alternative_type
                )
                db.add(selection_history)
            
            db.commit()
            
            if not is_already_applied:
                db.refresh(component)
            
            return {
                "component": component,
                "was_updated": not is_already_applied,
                "was_recorded": not is_same_selection,
                "message": _get_status_message(is_already_applied, is_same_selection)
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying rewritten text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying rewritten text: {str(e)}"
            )
        

    @staticmethod
    def expand_component(db: Session, component_id: UUID) -> Dict[str, Any]:
        """
        Expand a component's content using AI while maintaining its meaning.
        Returns multiple alternative expanded versions.
        """
        # Get the component with validation
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Only allow expansion for supported component types
        if component.component_type not in [ComponentType.ACTION, ComponentType.DIALOGUE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot expand component of type {component.component_type}"
            )
        
        # Get segment for context
        segment = db.query(SceneSegment).filter(
            SceneSegment.id == component.scene_segment_id
        ).first()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent segment not found"
            )
        
        # Get script for genre information
        script = db.query(Script).filter(Script.id == segment.script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Initialize OpenAI service
        openai_service = AzureOpenAIService()
        
        # Process based on component type
        try:
            if component.component_type == ComponentType.ACTION:
                alternatives = openai_service.expand_action_component(
                    text=component.content,
                    context={
                        "genre": script.genre,
                        "script_title": script.title
                    }
                )
            elif component.component_type == ComponentType.DIALOGUE:
                alternatives = openai_service.expand_dialogue_component(
                    text=component.content,
                    character_name=component.character_name,
                    context={
                        "genre": script.genre,
                        "script_title": script.title,
                        "parenthetical": component.parenthetical
                    }
                )
            
            # Delete any existing alternatives
            db.query(ExpansionAlternative).filter(
                ExpansionAlternative.component_id == component_id
            ).delete(synchronize_session=False)
            
            # Store themed alternatives in database
            db_alternatives = []
            
            # Concise alternative
            concise = ExpansionAlternative(
                component_id=component_id,
                alternative_type=ExpansionAlternativeType.CONCISE,
                expanded_text=alternatives.concise.expanded_text,
                explanation=alternatives.concise.explanation
            )
            db.add(concise)
            db_alternatives.append((ExpansionAlternativeType.CONCISE, concise))
            
            # Dramatic alternative
            dramatic = ExpansionAlternative(
                component_id=component_id,
                alternative_type=ExpansionAlternativeType.DRAMATIC,
                expanded_text=alternatives.dramatic.expanded_text,
                explanation=alternatives.dramatic.explanation
            )
            db.add(dramatic)
            db_alternatives.append((ExpansionAlternativeType.DRAMATIC, dramatic))
            
            # Minimal alternative
            minimal = ExpansionAlternative(
                component_id=component_id,
                alternative_type=ExpansionAlternativeType.MINIMAL,
                expanded_text=alternatives.minimal.expanded_text,
                explanation=alternatives.minimal.explanation
            )
            db.add(minimal)
            db_alternatives.append((ExpansionAlternativeType.MINIMAL, minimal))
            
            # Poetic alternative
            poetic = ExpansionAlternative(
                component_id=component_id,
                alternative_type=ExpansionAlternativeType.POETIC,
                expanded_text=alternatives.poetic.expanded_text,
                explanation=alternatives.poetic.explanation
            )
            db.add(poetic)
            db_alternatives.append((ExpansionAlternativeType.POETIC, poetic))
            
            # Humorous alternative
            humorous = ExpansionAlternative(
                component_id=component_id,
                alternative_type=ExpansionAlternativeType.HUMOROUS,
                expanded_text=alternatives.humorous.expanded_text,
                explanation=alternatives.humorous.explanation
            )
            db.add(humorous)
            db_alternatives.append((ExpansionAlternativeType.HUMOROUS, humorous))
            
            db.commit()
            
            # Create response object
            return ExpandComponentResponse(
                component_id=component_id,
                original_text=component.content,
                concise=ScriptExpansion(
                    expanded_text=alternatives.concise.expanded_text,
                    explanation=alternatives.concise.explanation
                ),
                dramatic=ScriptExpansion(
                    expanded_text=alternatives.dramatic.expanded_text,
                    explanation=alternatives.dramatic.explanation
                ),
                minimal=ScriptExpansion(
                    expanded_text=alternatives.minimal.expanded_text,
                    explanation=alternatives.minimal.explanation
                ),
                poetic=ScriptExpansion(
                    expanded_text=alternatives.poetic.expanded_text,
                    explanation=alternatives.poetic.explanation
                ),
                humorous=ScriptExpansion(
                    expanded_text=alternatives.humorous.expanded_text,
                    explanation=alternatives.humorous.explanation
                )
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating expansion alternatives: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating expansion alternatives: {str(e)}"
            )

    @staticmethod
    def apply_expansion_alternative(
        db: Session, 
        component_id: UUID, 
        expanded_text: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a selected expansion alternative to a component and record the selection.
        Only updates if the content would change and only records selection if different from current.
        
        Args:
            db: Database session
            component_id: ID of the component to update
            expanded_text: Text of the selected expansion to apply
            user_id: ID of the user making the selection
            
        Returns:
            Dictionary with updated component and status information
            
        Raises:
            HTTPException: If component or alternative not found, or on database error
        """
        def _get_status_message(is_already_applied: bool, is_same_selection: bool) -> str:
            """Generate an appropriate status message based on what happened."""
            if is_already_applied and is_same_selection:
                return "This alternative is already applied and was previously selected."
            elif is_already_applied:
                return "This alternative was already applied, but your selection has been recorded."
            elif is_same_selection:
                return "Component content updated, but this selection type was already recorded."
            else:
                return "Alternative successfully applied and recorded."
        
        # Find the component
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Get the specific alternative
        alternative = db.query(ExpansionAlternative).filter(
            and_(
                ExpansionAlternative.component_id == component_id,
                ExpansionAlternative.expanded_text == expanded_text,
                ExpansionAlternative.is_deleted.is_(False)
            )
        ).first()
        
        if not alternative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alternative with the provided expanded text not found"
            )
        
        try:
            # Check if the component already has this alternative's content
            is_already_applied = component.content == alternative.expanded_text
            
            # Get the most recent selection for this component (if any)
            latest_selection = db.query(ExpansionSelectionHistory).filter(
                ExpansionSelectionHistory.component_id == component_id
            ).order_by(
                ExpansionSelectionHistory.selected_at.desc()
            ).first()
            
            is_same_selection = False
            if latest_selection and latest_selection.alternative_type == alternative.alternative_type:
                is_same_selection = True
                
            # Only update and record if something would change
            if not is_already_applied:
                # Update the component with the selected alternative's text
                component.content = alternative.expanded_text
                component.updated_at = func.now()
            
            # Only add to history if this is a different selection than the most recent one
            if not is_same_selection:
                # Record this selection in the history table
                selection_history = ExpansionSelectionHistory(
                    user_id=user_id,
                    component_id=component_id,
                    alternative_id=alternative.id,
                    alternative_type=alternative.alternative_type
                )
                db.add(selection_history)
            
            db.commit()
            
            if not is_already_applied:
                db.refresh(component)
            
            return {
                "component": component,
                "was_updated": not is_already_applied,
                "was_recorded": not is_same_selection,
                "message": _get_status_message(is_already_applied, is_same_selection)
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying expanded text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying expanded text: {str(e)}"
            )
        
    @staticmethod
    def continue_component(db: Session, component_id: UUID) -> Dict[str, Any]:
        """
        Continue a component's content using AI while maintaining its meaning and style.
        Returns multiple alternative themed continuations.
        """
        # Get the component with validation
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Only allow continuation for supported component types
        if component.component_type not in [ComponentType.ACTION, ComponentType.DIALOGUE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot continue component of type {component.component_type}"
            )
        
        # Get segment for context
        segment = db.query(SceneSegment).filter(
            SceneSegment.id == component.scene_segment_id
        ).first()
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent segment not found"
            )
        
        # Get script for genre information
        script = db.query(Script).filter(Script.id == segment.script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Get additional character context if available
        character_traits = ""
        if component.component_type == ComponentType.DIALOGUE and component.character_name:
            # Here you could potentially look up character information from a character database
            # For now, we'll leave it blank or could derive from previous dialogues
            pass
        
        # Initialize OpenAI service
        openai_service = AzureOpenAIService()
        
        # Process based on component type
        try:
            if component.component_type == ComponentType.ACTION:
                alternatives = openai_service.continue_action_component(
                    text=component.content,
                    context={
                        "genre": script.genre,
                        "script_title": script.title
                    }
                )
            elif component.component_type == ComponentType.DIALOGUE:
                alternatives = openai_service.continue_dialogue_component(
                    text=component.content,
                    character_name=component.character_name,
                    context={
                        "genre": script.genre,
                        "script_title": script.title,
                        "parenthetical": component.parenthetical,
                        "character_traits": character_traits
                    }
                )
            
            # Delete any existing alternatives
            db.query(ContinuationAlternative).filter(
                ContinuationAlternative.component_id == component_id
            ).delete(synchronize_session=False)
            
            # Store themed alternatives in database
            db_alternatives = []
            
            # Concise alternative
            concise = ContinuationAlternative(
                component_id=component_id,
                alternative_type=ContinuationAlternativeType.CONCISE,
                continuation_text=alternatives.concise.continuation_text,
                explanation=alternatives.concise.explanation
            )
            db.add(concise)
            db_alternatives.append((ContinuationAlternativeType.CONCISE, concise))
            
            # Dramatic alternative
            dramatic = ContinuationAlternative(
                component_id=component_id,
                alternative_type=ContinuationAlternativeType.DRAMATIC,
                continuation_text=alternatives.dramatic.continuation_text,
                explanation=alternatives.dramatic.explanation
            )
            db.add(dramatic)
            db_alternatives.append((ContinuationAlternativeType.DRAMATIC, dramatic))
            
            # Minimal alternative
            minimal = ContinuationAlternative(
                component_id=component_id,
                alternative_type=ContinuationAlternativeType.MINIMAL,
                continuation_text=alternatives.minimal.continuation_text,
                explanation=alternatives.minimal.explanation
            )
            db.add(minimal)
            db_alternatives.append((ContinuationAlternativeType.MINIMAL, minimal))
            
            # Poetic alternative
            poetic = ContinuationAlternative(
                component_id=component_id,
                alternative_type=ContinuationAlternativeType.POETIC,
                continuation_text=alternatives.poetic.continuation_text,
                explanation=alternatives.poetic.explanation
            )
            db.add(poetic)
            db_alternatives.append((ContinuationAlternativeType.POETIC, poetic))
            
            # Humorous alternative
            humorous = ContinuationAlternative(
                component_id=component_id,
                alternative_type=ContinuationAlternativeType.HUMOROUS,
                continuation_text=alternatives.humorous.continuation_text,
                explanation=alternatives.humorous.explanation
            )
            db.add(humorous)
            db_alternatives.append((ContinuationAlternativeType.HUMOROUS, humorous))
            
            db.commit()
            
            # Create response object
            return ContinueComponentResponse(
                component_id=component_id,
                original_text=component.content,
                concise=ScriptContinuation(
                    continuation_text=alternatives.concise.continuation_text,
                    explanation=alternatives.concise.explanation
                ),
                dramatic=ScriptContinuation(
                    continuation_text=alternatives.dramatic.continuation_text,
                    explanation=alternatives.dramatic.explanation
                ),
                minimal=ScriptContinuation(
                    continuation_text=alternatives.minimal.continuation_text,
                    explanation=alternatives.minimal.explanation
                ),
                poetic=ScriptContinuation(
                    continuation_text=alternatives.poetic.continuation_text,
                    explanation=alternatives.poetic.explanation
                ),
                humorous=ScriptContinuation(
                    continuation_text=alternatives.humorous.continuation_text,
                    explanation=alternatives.humorous.explanation
                )
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating continuation alternatives: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating continuation alternatives: {str(e)}"
            )

    @staticmethod
    def apply_continuation_alternative(
        db: Session, 
        component_id: UUID, 
        continuation_text: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a selected continuation alternative to a component and record the selection.
        The continuation is appended to the existing content rather than replacing it.
        
        Args:
            db: Database session
            component_id: ID of the component to update
            continuation_text: Text of the selected continuation to apply
            user_id: ID of the user making the selection
            
        Returns:
            Dictionary with updated component and status information
        """
        def _get_status_message(is_already_applied: bool, is_same_selection: bool) -> str:
            """Generate an appropriate status message based on what happened."""
            if is_already_applied and is_same_selection:
                return "This continuation is already applied and was previously selected."
            elif is_already_applied:
                return "This continuation was already applied, but your selection has been recorded."
            elif is_same_selection:
                return "Component content updated, but this selection type was already recorded."
            else:
                return "Continuation successfully applied and recorded."
        
        # Find the component
        component = db.query(SceneSegmentComponent).filter(
            and_(
                SceneSegmentComponent.id == component_id,
                SceneSegmentComponent.is_deleted.is_(False)
            )
        ).first()
        
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found"
            )
        
        # Get the specific alternative
        alternative = db.query(ContinuationAlternative).filter(
            and_(
                ContinuationAlternative.component_id == component_id,
                ContinuationAlternative.continuation_text == continuation_text,
                ContinuationAlternative.is_deleted.is_(False)
            )
        ).first()
        
        if not alternative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Continuation alternative not found"
            )
        
        try:
            # For continuation, we need to check if the continuation has already been applied
            # by checking if the component content ends with the continuation text
            is_already_applied = component.content.endswith(continuation_text)
            
            # Get the most recent selection for this component (if any)
            latest_selection = db.query(ContinuationSelectionHistory).filter(
                ContinuationSelectionHistory.component_id == component_id
            ).order_by(
                ContinuationSelectionHistory.selected_at.desc()
            ).first()
            
            is_same_selection = False
            if latest_selection and latest_selection.alternative_type == alternative.alternative_type:
                is_same_selection = True
                
            # Only update if the continuation hasn't been applied yet
            if not is_already_applied:
                # For continuation, we append the text rather than replace it
                # Add a space between if needed
                if component.content and not component.content.endswith((" ", "\n")):
                    component.content = f"{component.content} {continuation_text}"
                else:
                    component.content = f"{component.content}{continuation_text}"
                    
                component.updated_at = func.now()
            
            # Only add to history if this is a different selection than the most recent one
            if not is_same_selection:
                # Record this selection in the history table
                selection_history = ContinuationSelectionHistory(
                    user_id=user_id,
                    component_id=component_id,
                    alternative_id=alternative.id,
                    alternative_type=alternative.alternative_type
                )
                db.add(selection_history)
            
            db.commit()
            
            if not is_already_applied:
                db.refresh(component)
            
            return {
                "component": component,
                "was_updated": not is_already_applied,
                "was_recorded": not is_same_selection,
                "message": _get_status_message(is_already_applied, is_same_selection)
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying continuation: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying continuation: {str(e)}"
            )
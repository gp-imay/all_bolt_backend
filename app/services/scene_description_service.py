# services/scene_description_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
# from sqlalchemy.sql import func
from fastapi import HTTPException, status
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
import logging
import json
import traceback

from models.scenes import SceneDescription
from models.beats import Beat
from models.script import Script
from models.beats import Beat, MasterBeatSheet

from schemas.scene import SceneCreate, SceneUpdate
from schemas.scene_description import SceneDescriptionResponse, SceneDescriptionResponsePost
from services.openai_service import AzureOpenAIService

logger = logging.getLogger(__name__)

class SceneDescriptionService:
    def __init__(self):
        self.openai_service = AzureOpenAIService()

    @staticmethod
    def format_scene_for_ui( scene_heading: str, scene_description: str) -> str:
        """Format scene details for UI display"""
        return f"{scene_heading} : {scene_description}"

    def prepare_scene_response(self, scene: SceneDescription) -> SceneDescriptionResponse:
        """Prepare scene response with UI-formatted details"""
        # logger.info(scene.scene_heading)
        # logger.info(scene.scene_description)
        return SceneDescriptionResponse(
            id=scene.id,
            beat_id=scene.beat_id,
            position=scene.position,
            scene_heading=scene.scene_heading,
            scene_description=scene.scene_description,
            scene_detail_for_ui=self.format_scene_for_ui(
                scene.scene_heading, 
                scene.scene_description
            ),
            created_at=scene.created_at,
            updated_at=scene.updated_at,
            is_deleted=scene.is_deleted,
            deleted_at=scene.deleted_at
        )

    @staticmethod
    def parse_scene_detail(scene_detail: str) -> tuple[str, str]:
        """
        Parse scene detail string in format 'Scene Title: {heading} : {description}'
        Returns tuple of (heading, description)
        """
        try:
            # Remove 'Scene Title: ' prefix
            # content = scene_detail.replace("Scene Title: ", "", 1)
            # Split remaining string on " : "
            logger.info("*"*100)
            logger.info(scene_detail)
            logger.info("*"*100)
            parts = scene_detail.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid scene detail format")
            return parts[0].strip(), parts[1].strip()
        except Exception as e:
            raise ValueError(f"Failed to parse scene detail: {str(e)}")

    @staticmethod
    def detect_changes(
        original_heading: str,
        original_description: str,
        new_heading: str,
        new_description: str
    ) -> dict:
        """
        Detect which fields have changed
        Returns dict with updated fields only
        """
        changes = {}
        if original_heading != new_heading:
            changes['scene_heading'] = new_heading
        if original_description != new_description:
            changes['scene_description'] = new_description
        return changes


    @staticmethod
    def get_beat_generation_context(
        # self,
        db: Session,
        beat_id: UUID,
        user_id: UUID
    ) -> Tuple[Beat, Script, Dict[str, Any], List[str]]:
        """
        Get all necessary context for scene generation
        """
        # Get beat with relationships
        # user_id = 'd6dc920c-acc2-40ce-8eaa-0d66c643ad1e'
        try:
            # First get the beat
            beat = db.query(Beat).filter(Beat.id == beat_id).first()
            if not beat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Beat not found"
                )
            # Then get the associated script
            script = db.query(Script).filter(
                and_(
                    Script.id == beat.script_id,
                    Script.user_id == user_id
                )
            ).first()
            if not script:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Script not found or unauthorized access"
                )

            # Finally get the master beat sheet
            master_beat_sheet = db.query(MasterBeatSheet).filter(
                MasterBeatSheet.id == beat.master_beat_sheet_id
            ).first()
            if not master_beat_sheet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Master beat sheet not found"
                )

        except Exception as e:
            logger.error(f"Error fetching beat data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching beat data: {str(e)}"
            )
        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat not found or unauthorized access"
            )


        # Parse template JSON
        template_data = master_beat_sheet.template
        if isinstance(template_data, str):
            template_data = json.loads(template_data)
        beat_template = next(
            (b for b in template_data['beats'] if b['position'] == beat.position),
            None
        )
        if not beat_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat template configuration not found"
            )

        # Get previous scenes if not first beat
        previous_scenes = []
        if beat.position > 1:
            previous_scenes = [
                scene.scene_heading 
                for scene in db.query(SceneDescription)
                .join(Beat)
                .filter(
                    and_(
                        Beat.script_id == script.id,
                        Beat.position < beat.position
                    )
                ).all()
            ]

        return beat, script, beat_template, previous_scenes



    async def generate_scene_description_for_beat(
        self,
        db: Session,
        beat_id: UUID,
        user_id: Optional[UUID]
    ) -> SceneDescriptionResponsePost:
        """
        Generate scenes for a beat using AI and save them to database
        """
        try:
            # user_id = 'd6dc920c-acc2-40ce-8eaa-0d66c643ad1e'
            # Get context from database
            beat, script, beat_template, previous_scenes = self.get_beat_generation_context(
                db, beat_id, user_id
            )
            
            # Get number of scenes from template
            num_scenes = beat_template.get('number_of_scenes', 4)

            # Check for existing scenes first
            existing_scenes = (
                db.query(SceneDescription)
                .filter(
                    and_(
                        SceneDescription.beat_id == beat_id,
                        SceneDescription.is_deleted.is_(False)
                    )
                )
                .order_by(SceneDescription.position)
                .all()
            )
            
            if existing_scenes:
                logger.info(f"Found {len(existing_scenes)} existing scenes for beat {beat_id}")
                return {
                    "success": True,
                    "context": {
                        "script_title": script.title,
                        "genre": script.genre,
                        "beat_position": beat.position,
                        "template_beat": beat_template,
                        "source": "existing"  # Indicate these are existing scenes
                    },
                    "generated_scenes": [
                        self.prepare_scene_response(scene)
                        for scene in existing_scenes
                    ]
                }


            # Generate scenes using OpenAI
            generated_scenes = self.openai_service.generate_scene_description_for_beat(
                story_synopsis=script.story,
                genre=script.genre,
                beat_position=beat.position,
                template_beat_title=beat_template['name'],
                template_beat_definition=beat_template['description'],
                story_specific_beat_title=beat.beat_title,
                story_specific_beat_description=beat.beat_description,
                previous_scenes=previous_scenes,
                num_scenes=num_scenes
            )
            stored_scenes = []
            for position, scene in enumerate(generated_scenes, 1):
                # Create SceneDescription object
                scene_description = SceneDescription(
                    beat_id=beat_id,
                    position=position,
                    scene_heading=scene.scene_heading,
                    scene_description=scene.scene_description,
                )
                
                db.add(scene_description)
                stored_scenes.append(scene_description)

            try:
                db.commit()
                # Refresh all scenes to get their generated IDs
                for scene in stored_scenes:
                    db.refresh(scene)
            except Exception as db_error:
                db.rollback()
                logger.error(f"Database error while storing scenes: {str(db_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store generated scenes in database"
                )
            return {
                "success": True,
                "context": {
                    "script_title": script.title,
                    "genre": script.genre,
                    "beat_position": beat.position,
                    "template_beat": beat_template,
                    "num_scenes": num_scenes
                },
                "generated_scenes": [
                    self.prepare_scene_response(scene)
                    for scene in stored_scenes
                ]
            }


        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Scene generation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate scenes: {str(e)}"
            )
        
    @staticmethod
    def get_scene_descriptions_for_beat(
        db: Session,
        beat_id: UUID,
        user_id: UUID
    ) -> List[SceneDescription]:
        """
        Retrieve all scene descriptions for a specific beat.
        
        Args:
            db: Database session
            beat_id: UUID of the beat
            user_id: UUID of the requesting user
            
        Returns:
            List of SceneDescription objects
            
        Raises:
            HTTPException: If beat not found or user unauthorized
        """
        try:
            # Verify beat exists and user has access
            beat_query = (
                db.query(Beat)
                .join(Script)
                .filter(
                    and_(
                        Beat.id == beat_id,
                        Script.user_id == user_id
                    )
                )
            )
            
            beat = beat_query.first()
            if not beat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Beat not found or unauthorized access"
                )
            
            # Get all non-deleted scene descriptions for this beat
            scene_descriptions = (
                db.query(SceneDescription)
                .filter(
                    and_(
                        SceneDescription.beat_id == beat_id,
                        SceneDescription.is_deleted.is_(False)
                    )
                )
                .order_by(SceneDescription.position)
                .all()
            )

            service = SceneDescriptionService()
            logger.info([vars(x) for x in scene_descriptions[:1]])
            return [service.prepare_scene_response(scene) for scene in scene_descriptions]

            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving scene descriptions: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve scene descriptions: {str(e)}"
            )

    async def update_scene_description(
        self,
        db: Session,
        scene_id: UUID,
        user_id: UUID,
        scene_detail: str
    ) -> SceneDescriptionResponse:
        """
        Update scene description based on edited UI string
        """
        try:
            # Get existing scene and verify ownership
            scene = (
                db.query(SceneDescription)
                .join(Beat)
                .join(Script)
                .filter(
                    and_(
                        SceneDescription.id == scene_id,
                        Script.user_id == user_id,
                        SceneDescription.is_deleted.is_(False)
                    )
                )
                .first()
            )

            if not scene:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scene not found or unauthorized access"
                )

            # Parse new scene detail
            try:
                new_heading, new_description = self.parse_scene_detail(scene_detail)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

            # Detect changes
            changes = self.detect_changes(
                scene.scene_heading,
                scene.scene_description,
                new_heading,
                new_description
            )

            if not changes:
                # No changes detected
                return self.prepare_scene_response(scene)

            # Apply updates
            for field, value in changes.items():
                setattr(scene, field, value)

            try:
                scene.updated_at = func.now()
                db.commit()
                db.refresh(scene)
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to update scene: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update scene"
                )

            return self.prepare_scene_response(scene)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating scene description: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update scene description: {str(e)}"
            )


    # @staticmethod
    # def get_scenes_for_beat(
    #     db: Session,
    #     beat_id: UUID,
    #     user_id: UUID
    # ) -> List[Scene]:
    #     """Get all scenes for a beat"""
    #     scenes = db.query(Scene).join(Beat).join(Script).filter(
    #         and_(
    #             Scene.beat_id == beat_id,
    #             Script.user_id == user_id,
    #             Scene.is_deleted.is_(False)
    #         )
    #     ).order_by(Scene.position).all()

    #     return scenes

    # @staticmethod
    # def update_scene(
    #     db: Session,
    #     scene_id: UUID,
    #     user_id: UUID,
    #     scene_update: SceneUpdate
    # ) -> Scene:
    #     """Update a scene"""
    #     scene = db.query(Scene).join(Beat).join(Script).filter(
    #         and_(
    #             Scene.id == scene_id,
    #             Script.user_id == user_id,
    #             Scene.is_deleted.is_(False)
    #         )
    #     ).first()

    #     if not scene:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="Scene not found or unauthorized access"
    #         )

    #     update_data = scene_update.model_dump(exclude_unset=True)
    #     for field, value in update_data.items():
    #         setattr(scene, field, value)

    #     try:
    #         db.commit()
    #         db.refresh(scene)
    #         return scene
    #     except Exception as e:
    #         db.rollback()
    #         logger.error(f"Failed to update scene: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Failed to update scene"
    #         )

    # @staticmethod
    # def delete_scene(
    #     db: Session,
    #     scene_id: UUID,
    #     user_id: UUID
    # ) -> bool:
    #     """Soft delete a scene"""
    #     scene = db.query(Scene).join(Beat).join(Script).filter(
    #         and_(
    #             Scene.id == scene_id,
    #             Script.user_id == user_id,
    #             Scene.is_deleted.is_(False)
    #         )
    #     ).first()

    #     if not scene:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="Scene not found or unauthorized access"
    #         )

    #     scene.soft_delete()
    #     try:
    #         db.commit()
    #         return True
    #     except Exception as e:
    #         db.rollback()
    #         logger.error(f"Failed to delete scene: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Failed to delete scene"
    #         )
        



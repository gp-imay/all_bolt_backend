# services/scene_description_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
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
from services.openai_service import AzureOpenAIService

logger = logging.getLogger(__name__)

class SceneDescriptionService:
    def __init__(self):
        self.openai_service = AzureOpenAIService()

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
        logger.info(template_data)
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
    ) -> List[SceneDescription]:
        """
        Generate scenes for a beat using AI and save them to database
        """
        try:
            # user_id = 'd6dc920c-acc2-40ce-8eaa-0d66c643ad1e'
            # Get context from database
            beat, script, beat_template, previous_scenes = self.get_beat_generation_context(
                db, beat_id, user_id
            )
            
            logger.info("Passed here")
            logger.info("*"*100)
            # Get number of scenes from template
            num_scenes = beat_template.get('number_of_scenes', 4)

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

            return {
                "success": True,
                "context": {
                    "script_title": script.title,
                    "genre": script.genre,
                    "beat_position": beat.position,
                    "template_beat": beat_template,
                    "num_scenes": num_scenes
                },
                "generated_scenes": [scene.model_dump() for scene in generated_scenes]
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
        



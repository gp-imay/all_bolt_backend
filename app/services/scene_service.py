from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging
import traceback

from app.models.beats import Scene, Beat, SceneGenerationTracker, SceneGenerationStatus, ActEnum
from app.models.script import Script
from app.schemas.scene import SceneCreate, SceneUpdate, SceneGenerationRequest
from app.schemas.scene import SceneResponse, SceneGenerationResult
from app.services.openai_service import AzureOpenAIService

logger = logging.getLogger(__name__)

class SceneService:
    @staticmethod
    def create_scene(db: Session, scene: SceneCreate) -> Scene:
        """Create a new scene"""
        # Verify beat exists and user has access
        beat = db.query(Beat).filter(Beat.id == scene.beat_id).first()
        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat not found"
            )

        # Calculate position if not provided
        if scene.position is None:
            scene.position = Scene.calculate_position(
                db=db,
                beat_id=scene.beat_id,
                target_position=float('inf')  # Add to end
            )

        # Create scene
        db_scene = Scene(**scene.model_dump())
        try:
            db.add(db_scene)
            db.commit()
            db.refresh(db_scene)
            return db_scene
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating scene: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create scene"
            )

    @staticmethod
    def get_scenes_for_beat(db: Session, beat_id: UUID) -> List[Scene]:
        """Get all scenes for a beat ordered by position"""
        return db.query(Scene)\
            .filter(
                Scene.beat_id == beat_id,
                Scene.is_deleted.is_(False)
            )\
            .order_by(Scene.position)\
            .all()

    @staticmethod
    def update_scene(db: Session, scene_id: UUID, scene_update: SceneUpdate) -> Scene:
        """Update a scene"""
        scene = db.query(Scene).filter(
            Scene.id == scene_id,
            Scene.is_deleted.is_(False)
        ).first()
        
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )

        update_data = scene_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scene, field, value)

        try:
            db.commit()
            db.refresh(scene)
            return scene
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating scene: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update scene"
            )

    @staticmethod
    def reorder_scene(db: Session, scene_id: UUID, new_position: float) -> Scene:
        """Reorder a scene within its beat"""
        scene = db.query(Scene).filter(
            Scene.id == scene_id,
            Scene.is_deleted.is_(False)
        ).first()
        
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )

        # Calculate new position
        new_pos = Scene.calculate_position(
            db=db,
            beat_id=scene.beat_id,
            target_position=new_position
        )
        
        scene.position = new_pos
        try:
            db.commit()
            db.refresh(scene)
            return scene
        except Exception as e:
            db.rollback()
            logger.error(f"Error reordering scene: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not reorder scene"
            )

    @staticmethod
    def delete_scene(db: Session, scene_id: UUID):
        """Soft delete a scene"""
        scene = db.query(Scene).filter(
            Scene.id == scene_id,
            Scene.is_deleted.is_(False)
        ).first()
        
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )

        scene.soft_delete()
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting scene: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete scene"
            )

    @staticmethod
    def get_existing_scenes(db: Session, beat_id: UUID) -> List[Scene]:
        """Get existing non-deleted scenes for a beat"""
        return db.query(Scene).filter(
            Scene.beat_id == beat_id,
            Scene.is_deleted.is_(False)
        ).order_by(Scene.position).all()
    
    @staticmethod
    def validate_beat_and_script(db: Session, beat_id: UUID, script_id: UUID) -> Tuple[Beat, Script]:
        """Validate and return beat and script"""
        beat = db.query(Beat).filter(Beat.id == beat_id).first()
        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat not found"
            )
        
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
            
        return beat, script



class SceneGenerationService:
    def __init__(self):
        self.openai_service = AzureOpenAIService()

    async def generate_scenes(
        self,
        db: Session,
        request: SceneGenerationRequest
    ) -> SceneGenerationResult:
        """Generate scenes for either a beat or an act"""
        # Create generation tracker
        tracker = SceneGenerationTracker(
            script_id=request.script_id,
            beat_id=request.beat_id,
            act=request.act,
            status=SceneGenerationStatus.IN_PROGRESS
        )
        db.add(tracker)
        db.flush()

        try:
            if request.beat_id:
                resp = await self._generate_scenes_for_beat(db, request.beat_id, request.script_id, tracker)
                return resp
            else:
                return await self._generate_scenes_for_act(db, request.script_id, request.act, tracker)
        except Exception as e:
            logger.error(traceback.format_exc())
            tracker.status = SceneGenerationStatus.FAILED
            db.commit()
            logger.error(f"Scene generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scene generation failed: {str(e)}"
            )

    async def _generate_scenes_for_beat(
        self,
        db: Session,
        beat_id: UUID,
        script_id: UUID,
        tracker: SceneGenerationTracker
    ) -> SceneGenerationResult:
        """Generate scenes for a single beat"""
        beat = db.query(Beat).filter(Beat.id == beat_id).first()
        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat not found"
            )
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )

        # Validate beat and script
        beat_, script_ = SceneService.validate_beat_and_script(db, beat_id, script_id)
        
        # Check for existing scenes
        existing_scenes = SceneService.get_existing_scenes(db, beat_id)
        if existing_scenes:
            logger.info(f"Found existing scenes for beat {beat_id}")
            return {
                "beat_id": beat.id,
                "scenes": existing_scenes,
                "source": "existing"
            }

        # Generate scenes using OpenAI
        scenes_data = self.openai_service.generate_scenes_for_beat(
                beat_title=beat.beat_title,
                beat_description=beat.beat_description,
                script_genre=script.genre,
                tone=None
            )
     
        # logger.info(type(scenes_data[0].dialogue_blocks))
        # Create scenes
        created_scenes = []

        for i, scene_data in enumerate(scenes_data, 1):
            dialogue_blocks_dict = [
                {
                    "character_name": block.character_name,
                    "dialogue": block.dialogue,
                    "parenthetical": block.parenthetical,
                    "position": block.position
                }
                for block in scene_data.dialogue_blocks
            ] if scene_data.dialogue_blocks else []

            scene = SceneCreate(
                beat_id=beat_id,
                position=i * 1000.0,  # Space them out
                scene_heading=scene_data.scene_heading,
                scene_description=scene_data.scene_description,
                dialogue_blocks=dialogue_blocks_dict,
                scene_hestimated_durationeading=scene_data.estimated_duration,
            )
            created_scenes.append(SceneService.create_scene(db, scene))

        # Update tracker
        tracker.status = SceneGenerationStatus.COMPLETED
        tracker.completed_at = func.now()
        db.commit()

        return SceneGenerationResult(
                beat_id=beat.id,
                scenes=[SceneResponse.model_validate(scene) for scene in created_scenes],
                source="generated"
            )


    async def _generate_scenes_for_act(
        self,
        db: Session,
        script_id: UUID,
        act: ActEnum,
        tracker: SceneGenerationTracker
    ) -> Dict[str, Any]:
        """Generate scenes for all beats in an act"""
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )

        beats = db.query(Beat).filter(
            and_(
                Beat.script_id == script_id,
                Beat.beat_act == act
            )
        ).order_by(Beat.position).all()

        if not beats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No beats found for act {act}"
            )

        results = []
        for beat in beats:
            beat_result = await self._generate_scenes_for_beat(
                db,
                beat.id,
                script.id,
                tracker
            )
            results.append(beat_result)

        tracker.status = SceneGenerationStatus.COMPLETED
        tracker.completed_at = func.now()
        db.commit()

        return {
            "act": act,
            "beats": results,
            "status": "completed"
        }

    @staticmethod
    def get_generation_status(
        db: Session,
        script_id: UUID,
        beat_id: Optional[UUID] = None,
        act: Optional[ActEnum] = None
    ) -> List[SceneGenerationTracker]:
        """Get status of scene generation"""
        query = db.query(SceneGenerationTracker).filter(
            SceneGenerationTracker.script_id == script_id
        )

        if beat_id:
            query = query.filter(SceneGenerationTracker.beat_id == beat_id)
        if act:
            query = query.filter(SceneGenerationTracker.act == act)

        return query.order_by(desc(SceneGenerationTracker.started_at)).all()
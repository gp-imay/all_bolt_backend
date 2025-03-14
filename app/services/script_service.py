# app/services/script_service.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
import traceback
import logging

logger = logging.getLogger(__name__)

from app.models.script import Script, ScriptCreationMethod
from app.models.beats import Beat, MasterBeatSheet, BeatSheetType, ActEnum
from app.schemas.script import ScriptCreate, ScriptUpdate
from app.schemas.beat import ScriptWithBeatsResponse, BeatResponse

from app.services.openai_service import AzureOpenAIService


class ScriptService:
    @staticmethod
    def create_script(db: Session, script: ScriptCreate, user_id: UUID) -> Script:
        """
        Create a new script
        """
        db_script = Script(
            **script.model_dump(),
            user_id=user_id
        )
        db.add(db_script)
        db.commit()
        db.refresh(db_script)
        return db_script

    @staticmethod
    def get_script(db: Session, script_id: UUID) -> Script:
        """
        Get a specific script by ID
        """
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        return script

    @staticmethod
    def get_scripts(
        db: Session, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 10,
        genre: Optional[str] = None
    ) -> List[Script]:
        """
        Get all scripts with optional filtering
        """
        query = db.query(Script).filter(Script.user_id == user_id)
        
        if genre:
            query = query.filter(Script.genre == genre)
            
        return query.order_by(desc(Script.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def update_script(
        db: Session, 
        script_id: UUID, 
        script_update: ScriptUpdate
    ) -> Script:
        """
        Update a script
        """
        script = ScriptService.get_script(db, script_id)
        update_data = script_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(script, field, value)
            
        db.commit()
        db.refresh(script)
        return script

    @staticmethod
    def delete_script(db: Session, script_id: UUID):
        """
        Delete a script
        """
        script = ScriptService.get_script(db, script_id)
        db.delete(script)
        db.commit()
        return True

    @staticmethod
    def get_user_scripts(
        db: Session, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 10
    ) -> List[Script]:
        """
        Get all scripts for a specific user
        """
        return db.query(Script)\
            .filter(Script.user_id == user_id)\
            .order_by(desc(Script.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def has_beat_sheet(db: Session, script_id: UUID) -> bool:
        """
        Check if a script has an associated beat sheet
        """
        return db.query(Beat).filter(Beat.script_id == script_id).first() is not None

    @staticmethod
    def create_script_with_beats(
        db: Session, 
        script: ScriptCreate, 
        user_id: UUID
    ) -> ScriptWithBeatsResponse:
        try:
            # Start transaction
            db_script = Script(
                **script.model_dump(),
                user_id=user_id
            )
            db.add(db_script)
            db.flush()  # Get script ID without committing

            # Get master beat sheet ID for Blake Snyder
            master_beat_sheet = db.query(MasterBeatSheet).filter(
                MasterBeatSheet.beat_sheet_type == BeatSheetType.BLAKE_SNYDER
            ).first()
            if not master_beat_sheet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Master beat sheet not found"
                )

            # Generate beats using OpenAI
            openai_service = AzureOpenAIService()
            generated_beats = openai_service.generate_beat_sheet(
                title=script.title,
                subtitle=script.subtitle or "",
                genre=script.genre,
                story=script.story
            )

            # Create beat records
            db_beats = []
            for i, beat in enumerate(generated_beats, 1):
                db_beat = Beat(
                    script_id=db_script.id,
                    master_beat_sheet_id=master_beat_sheet.id,
                    position=i,
                    beat_title=beat.beat_title,
                    beat_description=beat.description,
                    beat_act=ActEnum(beat.act)  # Add the act from the model response
                )
                
                # Store complete JSON only for first beat
                if i == 1:
                    db_beat.complete_json = [b.model_dump() for b in generated_beats]
                
                db_beats.append(db_beat)
                db.add(db_beat)

            # Commit transaction
            db.commit()
            
            # Prepare response
            return ScriptWithBeatsResponse(
                script=db_script,
                beats=[BeatResponse(
                    position=beat.position,
                    beat_title=beat.beat_title,
                    beat_description=beat.beat_description,
                    beat_id=beat.id,
                    beat_act=beat.beat_act,
                    script_id=beat.script_id
                ) for beat in db_beats]
            )

        except Exception as e:
            logger.error(traceback.format_exc())
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating script with beats: {str(e)}"
            )
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
import logging

from models.script import Script
from models.beats import Beat, MasterBeatSheet, BeatSheetType
from schemas.beat import BeatCreate, BeatUpdate
from schemas.script import ScriptCreationMethod

logger = logging.getLogger(__name__)

class BeatSheetService:
    @staticmethod
    def create_beat_sheet(
        db: Session,
        script_id: UUID,
        user_id: UUID,
        beats_data: List[dict]
    ) -> List[Beat]:
        """
        Create a new beat sheet for a script
        """
        # Verify script exists and belongs to user
        script = db.query(Script).filter(
            and_(Script.id == script_id, Script.user_id == user_id)
        ).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found or unauthorized access"
            )

        # Get the master beat sheet for Blake Snyder
        master_beat_sheet = db.query(MasterBeatSheet).filter(
            MasterBeatSheet.beat_sheet_type == BeatSheetType.BLAKE_SNYDER
        ).first()
        if not master_beat_sheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master beat sheet template not found"
            )

        try:
            # Create beats
            beats = []
            for position, beat_data in enumerate(beats_data, start=1):
                beat = Beat(
                    script_id=script_id,
                    user_id=user_id,
                    master_beat_sheet_id=master_beat_sheet.id,
                    position=position,
                    beat_title=beat_data['beat_title'],
                    beat_description=beat_data['beat_description']
                )
                db.add(beat)
                beats.append(beat)

            db.commit()
            for beat in beats:
                db.refresh(beat)
            return beats

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating beat sheet: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating beat sheet: {str(e)}"
            )

    @staticmethod
    def get_beat_sheet(
        db: Session,
        script_id: UUID,
        user_id: UUID
    ) -> List[Beat]:
        """
        Get all beats for a script
        """
        beats = db.query(Beat).filter(
            and_(
                Beat.script_id == script_id,
                Beat.user_id == user_id
            )
        ).order_by(Beat.position).all()

        if not beats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat sheet not found"
            )
        
        return beats

    @staticmethod
    def update_beat(
        db: Session,
        script_id: UUID,
        user_id: UUID,
        position: int,
        beat_update: BeatUpdate
    ) -> Beat:
        """
        Update a specific beat
        """
        beat = db.query(Beat).filter(
            and_(
                Beat.script_id == script_id,
                Beat.user_id == user_id,
                Beat.position == position
            )
        ).first()

        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Beat at position {position} not found"
            )

        update_data = beat_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(beat, field, value)

        try:
            db.commit()
            db.refresh(beat)
            return beat
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating beat: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating beat: {str(e)}"
            )

    @staticmethod
    def delete_beat_sheet(
        db: Session,
        script_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete all beats for a script
        """
        result = db.query(Beat).filter(
            and_(
                Beat.script_id == script_id,
                Beat.user_id == user_id
            )
        ).delete(synchronize_session=False)

        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat sheet not found"
            )

        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting beat sheet: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting beat sheet: {str(e)}"
            )
        
    @staticmethod
    def get_script_beatsheet(
        db: Session,
        script_id: UUID,
        user_id: UUID
    ) -> List[Beat]:
        """
        Get and validate a script's beat sheet
        """
        # Get script and verify ownership
        script = db.query(Script).filter(
            and_(
                Script.id == script_id,
                Script.user_id == user_id
            )
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
                detail="Script was not created with AI assistance"
            )
        
        # Get beats and master beat sheet info
        beats_query = db.query(
            Beat, MasterBeatSheet.number_of_beats
        ).join(
            MasterBeatSheet,
            Beat.master_beat_sheet_id == MasterBeatSheet.id
        ).filter(
            Beat.script_id == script_id
        )
        
        beats = [beat for beat, _ in beats_query.all()]
        if not beats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beat sheet not found"
            )
        
        required_beats = beats_query.first()[1]  # Get number_of_beats from first result
        
        # Verify completeness
        if len(beats) < required_beats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Beat sheet generation is incomplete. Expected {required_beats} beats, found {len(beats)}"
            )
        
        return sorted(beats, key=lambda x: x.position)
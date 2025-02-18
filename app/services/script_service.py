# app/services/script_service.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID

from models.script import Script
from schemas.script import ScriptCreate, ScriptUpdate

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

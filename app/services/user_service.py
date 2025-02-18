# app/services/user_service.py
from sqlalchemy.orm import Session
from models.users import User
from schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException, status
from datetime import datetime
from typing import Dict, Any

class UserService:
    @staticmethod
    def get_user(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_supabase_uid(db: Session, supabase_uid: str):
        return db.query(User).filter(User.supabase_uid == supabase_uid).first()

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100):
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create_user(db: Session, user_data: Dict[str, Any]):
        """Create user from Supabase JWT data"""
        try:
            user_create = UserCreate.from_jwt_payload(user_data)
            db_user = User(
                email=user_create.email,
                full_name=user_create.full_name,
                supabase_uid=user_create.supabase_uid,
                email_verified=user_create.email_verified,
                phone=user_create.phone,
                phone_verified=user_create.phone_verified,
                auth_provider=user_create.auth_provider,
                auth_role=user_create.auth_role,
                is_anonymous=user_create.is_anonymous,
                app_metadata=user_create.app_metadata,
                user_metadata=user_create.user_metadata,
                last_sign_in=datetime.fromtimestamp(user_data.get("iat", 0))
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create user: {str(e)}"
            )


    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate):
        db_user = UserService.get_user(db, user_id)
        update_data = user_update.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_user, key, value)
            
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int):
        user = UserService.get_user(db, user_id)
        db.delete(user)
        db.commit()
        return user
# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from jose import JWTError, jwt


from config import settings
from database import get_db
from schemas.user import UserOut, UserUpdate, UserCreate, Token
from services.user_service import UserService
from auth.dependencies import get_current_user, get_current_superuser
from schemas.script import ScriptList

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def read_user_me(current_user = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/register", response_model=UserOut)
async def register_user(
    token: Token,
    db: Session = Depends(get_db)
):
    """
    Register a new user with Supabase access token.
    If user already exists (based on supabase_uid), returns the existing user.
    """
    try:
        payload = jwt.decode(
            token.access_token.strip('"'),
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated"
        )
        supabase_uid = payload.get("sub")
        if not supabase_uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token: missing user ID"
            )
        existing_user = UserService.get_user_by_supabase_uid(db, supabase_uid)
        if existing_user:
            return existing_user
        user = UserService.create_user(db, payload)
        return user
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not register user: {str(e)}"
        )



@router.put("/me", response_model=UserOut)
async def update_user_me(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    return UserService.update_user(
        db=db,
        user_id=current_user.id,
        user_update=user_update
    )

@router.get("/me/scripts", response_model=List[ScriptList])
async def read_user_scripts(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scripts for the current user"""
    return UserService.get_user_scripts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

# Admin routes (protected by superuser)
@router.get("/", response_model=List[UserOut])
async def read_users(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    return UserService.get_users(db=db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserOut)
async def read_user(
    user_id: UUID,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user = UserService.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    user = UserService.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    UserService.delete_user(db=db, user_id=user_id)
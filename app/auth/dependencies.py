# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
# from jose import JWTError
# import jwt
from jose import JWTError, jwt
from database import get_db
from config import settings
from services.user_service import UserService
from typing import Optional
import json

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Validate access token and return current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated"
        )
        
        # Extract user info from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = UserService.get_user_by_supabase_uid(db, user_id)
        if user is None:
            user = UserService.create_user(db, payload)
            
        return user
        
    except JWTError:
        raise credentials_exception

async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Check if current user is active
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user = Depends(get_current_user)
):
    """
    Check if current user is superuser
    """
    if not current_user.auth_role == "service_role":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough privileges"
        )
    return current_user
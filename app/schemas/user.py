# app/schemas/user.py
from pydantic import BaseModel, EmailStr, UUID4, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.schemas.script import Script

class Token(BaseModel):
    access_token: str


class UserMetadata(BaseModel):
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = None
    full_name: Optional[str] = None
    phone_verified: Optional[bool] = None
    sub: Optional[str] = None

class AppMetadata(BaseModel):
    provider: str
    providers: List[str]

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    email_verified: bool = False
    phone_verified: bool = False
    auth_provider: str
    auth_role: str = "authenticated"
    is_anonymous: bool = False


class UserCreate(BaseModel):
    """Schema for creating a user from Supabase JWT"""
    email: EmailStr
    full_name: str
    supabase_uid: str
    email_verified: bool = False
    phone: Optional[str] = None
    phone_verified: bool = False
    auth_provider: Optional[str] = None
    auth_role: str = "authenticated"
    is_anonymous: bool = False
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_jwt_payload(cls, payload: Dict[str, Any]):
        return cls(
            email=payload["email"],
            full_name=payload["user_metadata"]["full_name"],
            supabase_uid=payload["sub"],
            email_verified=payload["user_metadata"].get("email_verified", False),
            phone=payload.get("phone", ""),
            phone_verified=payload["user_metadata"].get("phone_verified", False),
            auth_provider=payload["app_metadata"].get("provider"),
            auth_role=payload.get("role", "authenticated"),
            is_anonymous=payload.get("is_anonymous", False),
            app_metadata=payload.get("app_metadata"),
            user_metadata=payload.get("user_metadata")
        )


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None
    scripts: List[Script] = []

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    """Schema for public user information"""
    id: UUID4
    email: EmailStr
    full_name: str
    is_active: bool
    auth_role: str
    email_verified: bool

    class Config:
        from_attributes = True
# app/models/user.py
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import UUIDModel

class User(UUIDModel):
    __tablename__ = "users"

    # Core fields from Supabase JWT
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    supabase_uid = Column(String, nullable=False)
    
    # Metadata
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=False)
    
    # Auth metadata
    auth_role = Column(String, default='authenticated')  # from 'role' in JWT
    auth_provider = Column(String)  # from app_metadata.provider
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sign_in = Column(DateTime(timezone=True))  # Can be updated from JWT iat
    
    # Store full metadata for reference
    app_metadata = Column(JSON, nullable=True)
    user_metadata = Column(JSON, nullable=True)

    is_super_user = Column(Boolean, default=False)
    
    # Relationships
    scripts = relationship("Script", back_populates="user", cascade="all, delete-orphan")
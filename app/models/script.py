# app/models/script.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from models.base import UUIDModel

class Script(UUIDModel):
    __tablename__ = "scripts"

    title = Column(String(255), nullable=False, index=True)
    subtitle = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=False)
    story = Column(Text, nullable=False)
    is_file_uploaded = Column(Boolean, default=False, nullable=False)
    file_url = Column(String(512), nullable=True)  # For Azure Blob Storage URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    script_progress = Column(Integer, default=0, nullable=True)

    # Foreign key to user using UUID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Relationship with user
    user = relationship("User", back_populates="scripts")

    def __repr__(self):
        return f"<Script(id={self.id}, title={self.title}, genre={self.genre})>"
    
    __table_args__ = (
        CheckConstraint('my_column >= 0 AND my_column <= 100', name='check_my_column_range'),
    )

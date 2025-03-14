from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import UUIDModel, SoftDeleteMixin

class SceneDescription(UUIDModel, SoftDeleteMixin):
    __tablename__ = "scene_description_beats"

    beat_id = Column(UUID(as_uuid=True), ForeignKey("beats.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    scene_heading = Column(String(1000), nullable=False)
    scene_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    scene_segments = relationship("SceneSegment", back_populates="scene_description", cascade="all, delete-orphan")
    # Relationship with Beat
    # beat = relationship("Beat", back_populates="scene_descriptions")

    # __table_args__ = (
    #     UniqueConstraint('beat_id', 'position', name='unique_scene_position_per_beat'),
    # )

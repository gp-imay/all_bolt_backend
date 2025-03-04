# app/models/scene_segment.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
from typing import Optional

from models.base import UUIDModel, SoftDeleteMixin


class ComponentType(str, enum.Enum):
    HEADING = "HEADING"
    ACTION = "ACTION"
    DIALOGUE = "DIALOGUE"
    TRANSITION = "TRANSITION"
    CHARACTER = "CHARACTER"

class SceneSegment(UUIDModel, SoftDeleteMixin):
    """
    A segment of a screenplay scene.
    
    This model represents a distinct section within a screenplay. Each script can have
    multiple segments, and each segment can optionally be associated with a beat and/or
    scene description (depending on which workflow created it).
    """
    __tablename__ = "scene_segments"

    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    beat_id = Column(UUID(as_uuid=True), ForeignKey("beats.id", ondelete="SET NULL"), nullable=True)
    scene_description_id = Column(UUID(as_uuid=True), ForeignKey("scene_description_beats.id", ondelete="SET NULL"), nullable=True)
    segment_number = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    script = relationship("Script", back_populates="scene_segments")
    beat = relationship("Beat", back_populates="scene_segments")
    scene_description = relationship("SceneDescription", back_populates="scene_segments")
    components = relationship("SceneSegmentComponent", back_populates="scene_segment", cascade="all, delete-orphan")

    __table_args__ = (
        # Ensure unique ordering within a script (for non-deleted segments)
        # This is implemented using a partial index in PostgreSQL
    )


class SceneSegmentComponent(UUIDModel, SoftDeleteMixin):
    """
    A component within a scene segment.
    
    This model represents the various elements that make up a scene segment,
    such as headings, action descriptions, dialogue, or transitions.
    """
    __tablename__ = "scene_segment_components"

    scene_segment_id = Column(UUID(as_uuid=True), ForeignKey("scene_segments.id", ondelete="CASCADE"), nullable=False)
    component_type = Column(Enum(ComponentType), nullable=False)
    position = Column(Float, nullable=False)
    content = Column(Text, nullable=False)
    character_name = Column(String(255), nullable=True)  # Only for DIALOGUE type
    parenthetical = Column(Text, nullable=True)  # Only for DIALOGUE type
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    scene_segment = relationship("SceneSegment", back_populates="components")

    __table_args__ = (
        # Ensure unique ordering within a segment (for non-deleted components)
        # This is implemented using a partial index in PostgreSQL
    )
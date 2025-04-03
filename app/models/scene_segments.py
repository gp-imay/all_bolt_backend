# app/models/scene_segment.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Boolean, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
from typing import Optional

from app.models.base import UUIDModel, SoftDeleteMixin


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
    shortening_alternatives = relationship("ShorteningAlternative", back_populates="component", cascade="all, delete-orphan")
    rewrite_alternatives = relationship("RewriteAlternative", back_populates="component", cascade="all, delete-orphan")
    expansion_alternatives = relationship("ExpansionAlternative", back_populates="component", cascade="all, delete-orphan")
    continuation_alternatives = relationship("ContinuationAlternative", back_populates="component", cascade="all, delete-orphan")



    __table_args__ = (
        # Ensure unique ordering within a segment (for non-deleted components)
        # This is implemented using a partial index in PostgreSQL
    )


class ShorteningAlternative(UUIDModel, SoftDeleteMixin):
    """
    Stores AI-generated shortening alternatives for a component.
    """
    __tablename__ = "shortening_alternatives"

    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=True)
    shortened_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    component = relationship("SceneSegmentComponent", back_populates="shortening_alternatives")
    
    __table_args__ = (
        UniqueConstraint('component_id', 'alternative_type', name='unique_alternative_type_per_component'),
    )


class ShorteningSelectionHistory(UUIDModel):
    """
    Records each time a user selects and applies a shortening alternative.
    Provides analytics data on which alternative types are preferred.
    """
    __tablename__ = "shortening_selection_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_id = Column(UUID(as_uuid=True), ForeignKey("shortening_alternatives.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=False)
    selected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    component = relationship("SceneSegmentComponent")
    alternative = relationship("ShorteningAlternative")


class RewriteAlternative(UUIDModel, SoftDeleteMixin):
    """
    Stores AI-generated rewriting alternatives for a component.
    """
    __tablename__ = "rewrite_alternatives"

    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=True)
    rewritten_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    component = relationship("SceneSegmentComponent", back_populates="rewrite_alternatives")
    
    __table_args__ = (
        UniqueConstraint('component_id', 'alternative_type', name='unique_rewrite_alternative_type_per_component'),
    )


class RewriteSelectionHistory(UUIDModel):
    """
    Records each time a user selects and applies a rewrite alternative.
    Provides analytics data on which alternative types are preferred.
    """
    __tablename__ = "rewrite_selection_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_id = Column(UUID(as_uuid=True), ForeignKey("rewrite_alternatives.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=False)
    selected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    component = relationship("SceneSegmentComponent")
    alternative = relationship("RewriteAlternative")

# Add after the ShorteningAlternative model
class ExpansionAlternative(UUIDModel, SoftDeleteMixin):
    """
    Stores AI-generated expansion alternatives for a component.
    """
    __tablename__ = "expansion_alternatives"

    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=True)
    expanded_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    component = relationship("SceneSegmentComponent", back_populates="expansion_alternatives")
    
    __table_args__ = (
        UniqueConstraint('component_id', 'alternative_type', name='unique_expansion_alternative_type_per_component'),
    )

# Add after the ShorteningSelectionHistory model
class ExpansionSelectionHistory(UUIDModel):
    """
    Records each time a user selects and applies an expansion alternative.
    Provides analytics data on which alternative types are preferred.
    """
    __tablename__ = "expansion_selection_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_id = Column(UUID(as_uuid=True), ForeignKey("expansion_alternatives.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=False)
    selected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    component = relationship("SceneSegmentComponent")
    alternative = relationship("ExpansionAlternative")


class ContinuationAlternative(UUIDModel, SoftDeleteMixin):
    """
    Stores AI-generated continuation alternatives for a component.
    """
    __tablename__ = "continuation_alternatives"

    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=True)
    continuation_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    component = relationship("SceneSegmentComponent", back_populates="continuation_alternatives")
    
    __table_args__ = (
        UniqueConstraint('component_id', 'alternative_type', name='unique_continuation_alternative_type_per_component'),
    )


class ContinuationSelectionHistory(UUIDModel):
    """
    Records each time a user selects and applies a continuation alternative.
    Provides analytics data on which continuation types are preferred.
    """
    __tablename__ = "continuation_selection_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("scene_segment_components.id", ondelete="CASCADE"), nullable=False)
    alternative_id = Column(UUID(as_uuid=True), ForeignKey("continuation_alternatives.id", ondelete="CASCADE"), nullable=False)
    alternative_type = Column(Text, nullable=False)
    selected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    component = relationship("SceneSegmentComponent")
    alternative = relationship("ContinuationAlternative")
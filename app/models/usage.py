# app/models/usage.py
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import UUIDModel
import enum

class AICallTypeEnum(str, enum.Enum):
    BEAT_GENERATION = "beat_generation"
    SCENE_DESCRIPTION = "scene_description"
    SCENE_SEGMENT = "scene_segment"
    SHORTENING = "shortening"
    REWRITING = "rewriting"
    EXPANSION = "expansion"
    CONTINUATION = "continuation"

class AIUsageLog(UUIDModel):
    __tablename__ = "ai_usage_log"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    call_type = Column(Enum(AICallTypeEnum), nullable=False)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True)
    usage_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="ai_usage_logs")
    script = relationship("Script")
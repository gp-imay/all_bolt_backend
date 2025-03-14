from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Enum, Integer, UniqueConstraint, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import UUIDModel
import enum

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)

    def soft_delete(self):
        self.deleted_at = func.now()
        self.is_deleted = True


class BeatSheetType(str, enum.Enum):
    BLAKE_SNYDER = "Blake Snyder's Beat Sheet (Save the Cat!)"
    HERO_JOURNEY = "The Hero's Journey (Joseph Campbell / Christopher Vogler)"
    STORY_CIRCLE = "Dan Harmon's Story Circle"
    PIXAR_STRUCTURE = "Pixar Story Structure"
    TV_BEAT_SHEET = "TV Beat Sheet (TV Structure)"
    MINI_MOVIE = "The Mini-Movie Method (Chris Soth)"
    INDIE_FILM = "Indie Film Beat Sheet"

class ActEnum(str, enum.Enum):
    act_1 = "act_1"
    act_2a = "act_2a"
    act_2b = "act_2b"
    act_3 = "act_3"

class SceneGenerationStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MasterBeatSheet(UUIDModel):
    __tablename__ = "master_beat_sheets"

    name = Column(String(255), nullable=False)
    beat_sheet_type = Column(Enum(BeatSheetType), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    number_of_beats = Column(Integer, nullable=False)
    template = Column(JSON, nullable=False)  # Store the default beat names 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with Beat
    beats = relationship("Beat", back_populates="master_beat_sheet")

class Beat(UUIDModel, SoftDeleteMixin):
    __tablename__ = "beats"

    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    master_beat_sheet_id = Column(UUID(as_uuid=True), ForeignKey("master_beat_sheets.id"), nullable=False)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Added user_id
    position = Column(Integer, nullable=False)
    beat_title = Column(String(1000), nullable=False)
    beat_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    beat_act = Column(Enum(ActEnum), nullable=False)
    complete_json = Column(JSONB, nullable=True)

    # Relationships
    script = relationship("Script", back_populates="beats")
    master_beat_sheet = relationship("MasterBeatSheet", back_populates="beats")
    scenes = relationship("Scene", back_populates="beat", cascade="all, delete-orphan")
    generation_attempts = relationship("SceneGenerationTracker", back_populates="beat")
    scene_segments = relationship("SceneSegment", back_populates="beat", cascade="all, delete-orphan")

    # scene_descriptions = relationship("SceneDescription", back_populates="beats", cascade="all, delete-orphan")


    # user = relationship("User", back_populates="beats")  # Added relationship to user

    __table_args__ = (
        UniqueConstraint('script_id', 'position', name='unique_position_per_script'),
        UniqueConstraint('script_id', 'beat_title', name='unique_beat_title_per_script'),
    )


class Scene(UUIDModel, SoftDeleteMixin):
    __tablename__ = "scenes"

    beat_id = Column(UUID(as_uuid=True), ForeignKey("beats.id", ondelete="CASCADE"), nullable=False)
    position = Column(Float, nullable=False)  # Float for flexible ordering
    scene_heading = Column(String(1000), nullable=False)  # Longer length for detailed headings
    scene_description = Column(Text, nullable=False)
    dialogue_blocks = Column(JSONB, nullable=True)
    estimated_duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    beat = relationship("Beat", back_populates="scenes")

    __table_args__ = (
        UniqueConstraint('beat_id', 'position', 'is_deleted', name='unique_position_per_beat'),
    )

    # @classmethod
    # def calculate_position(cls, db, beat_id, target_position: float) -> float:
    #     """Calculate a new position value between two existing positions"""
    #     positions = db.query(cls.position)\
    #         .filter(cls.beat_id == beat_id, cls.is_deleted.is_(False))\
    #         .order_by(cls.position)\
    #         .all()
    #     positions = [p[0] for p in positions]
        
    #     if not positions:
    #         return 1000.0  # First item
            
    #     if target_position <= positions[0]:
    #         return positions[0] - 1000.0  # Position before first
            
    #     if target_position >= positions[-1]:
    #         return positions[-1] + 1000.0  # Position after last
            
    #     # Find position between two existing positions
    #     for i in range(len(positions) - 1):
    #         if positions[i] <= target_position <= positions[i + 1]:
    #             return (positions[i] + positions[i + 1]) / 2


class SceneGenerationTracker(UUIDModel, SoftDeleteMixin):
    __tablename__ = "scene_generation_tracker"
    
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id"), nullable=False)
    beat_id = Column(UUID(as_uuid=True), ForeignKey("beats.id"), nullable=True)
    act = Column(Enum(ActEnum), nullable=True)
    status = Column(Enum(SceneGenerationStatus), nullable=False, default=SceneGenerationStatus.NOT_STARTED)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, default=1)

    # Relationships
    script = relationship("Script", back_populates="scene_generations")
    beat = relationship("Beat", back_populates="generation_attempts")

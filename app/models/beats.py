from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Enum, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.base import UUIDModel
import enum

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

class Beat(UUIDModel):
    __tablename__ = "beats"

    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    master_beat_sheet_id = Column(UUID(as_uuid=True), ForeignKey("master_beat_sheets.id"), nullable=False)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Added user_id
    position = Column(Integer, nullable=False)
    beat_title = Column(String(255), nullable=False)
    beat_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    beat_act = Column(Enum(ActEnum), nullable=False)
    complete_json = Column(JSONB, nullable=True)
    # dummy_column = Column(Boolean, default=False)

    # Relationships
    script = relationship("Script", back_populates="beats")
    master_beat_sheet = relationship("MasterBeatSheet", back_populates="beats")
    # user = relationship("User", back_populates="beats")  # Added relationship to user

    __table_args__ = (
        UniqueConstraint('script_id', 'position', name='unique_position_per_script'),
        UniqueConstraint('script_id', 'beat_title', name='unique_beat_title_per_script'),
    )

    #   "beat_number": 1,
    #   "beat_name": "Opening Image",
    #   "beat_title": "Circle of Change",
    #   "description": "The film opens with an awe-inspiring sunrise over a modern Serengeti, symbolizing rebirth. We see a bustling pride of lions, their hierarchy intact, with King Mufasa overseeing the land. Young Simba is introduced as a playful cub who dreams of ruling someday. The scene sets the tone, contrasting tradition with the idea of an impending transformation.",
    #   "page_length": "1-3",
    #   "timing": "1%",
    #   "act": "act_1"
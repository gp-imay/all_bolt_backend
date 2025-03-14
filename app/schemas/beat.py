from pydantic import BaseModel, UUID4, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum



from app.schemas.script import ScriptOut

class BeatSheetType(str, Enum):
    BLAKE_SNYDER = "Blake Snyder's Beat Sheet (Save the Cat!)"
    HERO_JOURNEY = "The Hero's Journey (Joseph Campbell / Christopher Vogler)"
    STORY_CIRCLE = "Dan Harmon's Story Circle"
    PIXAR_STRUCTURE = "Pixar Story Structure"
    TV_BEAT_SHEET = "TV Beat Sheet (TV Structure)"
    MINI_MOVIE = "The Mini-Movie Method (Chris Soth)"
    INDIE_FILM = "Indie Film Beat Sheet"

class ActEnum(str, Enum):
    act_1 = "act_1"
    act_2a = "act_2a"
    act_2b = "act_2b"
    act_3 = "act_3"

class BeatBase(BaseModel):
    position: int = Field(..., ge=1, le=15)
    beat_title: str = Field(..., min_length=1, max_length=255)
    beat_description: str = Field(..., min_length=1)

class BeatCreate(BeatBase):
    script_id: UUID4
    master_beat_sheet_id: UUID4

class BeatUpdate(BaseModel):
    beat_title: Optional[str] = Field(None, min_length=1, max_length=255)
    beat_description: Optional[str] = Field(None, min_length=1)
    beat_act: Optional[ActEnum] = None


class Beat(BeatBase):
    id: UUID4
    script_id: UUID4
    master_beat_sheet_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MasterBeatSheetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    beat_sheet_type: BeatSheetType
    description: str
    number_of_beats: int = Field(..., ge=1)
    template: Dict[str, str]  # Key: beat name, Value: default description

class MasterBeatSheetCreate(MasterBeatSheetBase):
    pass

class MasterBeatSheet(MasterBeatSheetBase):
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for returning all beats of a script
class ScriptBeatSheet(BaseModel):
    script_id: UUID4
    beats: List[Beat]
    master_beat_sheet_id: UUID4
    beat_sheet_type: BeatSheetType


class BeatResponse(BaseModel):
    position: int
    beat_title: str
    beat_description: str
    beat_id: UUID4
    beat_act: str
    script_id: UUID4
    
class ScriptWithBeatsResponse(BaseModel):
    script: ScriptOut
    beats: List[BeatResponse]


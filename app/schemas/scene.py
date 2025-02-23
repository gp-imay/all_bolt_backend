from pydantic import BaseModel, UUID4, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DialogueBlock(BaseModel):
    character_name: str = Field(..., min_length=1)
    dialogue: str = Field(..., min_length=1)
    parenthetical: Optional[str] = None
    position: int = Field(...)

class SceneBase(BaseModel):
    scene_heading: str = Field(..., min_length=1, max_length=1000)
    scene_description: str = Field(..., min_length=1)
    dialogue_blocks: Optional[List[DialogueBlock]] = None
    estimated_duration: Optional[float] = Field(None, ge=0)

class SceneCreate(SceneBase):
    beat_id: UUID4
    position: Optional[float] = None

class SceneUpdate(BaseModel):
    scene_heading: Optional[str] = Field(None, min_length=1, max_length=1000)
    scene_description: Optional[str] = None
    dialogue_blocks: Optional[List[DialogueBlock]] = None
    estimated_duration: Optional[float] = Field(None, ge=0)
    position: Optional[float] = None

class Scene(SceneBase):
    id: UUID4
    beat_id: UUID4
    position: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Scene Generation Related Schemas
class SceneGenerationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ActEnum(str, Enum):
    act_1 = "act_1"
    act_2a = "act_2a"
    act_2b = "act_2b"
    act_3 = "act_3"

class SceneGenerationRequest(BaseModel):
    beat_id: Optional[UUID4] = None  # For single beat generation
    act: Optional[ActEnum] = None    # For act-level generation
    script_id: UUID4

    @validator('*', pre=True)
    def validate_mutually_exclusive(cls, v, values):
        if 'beat_id' in values and 'act' in values:
            if values['beat_id'] is not None and values['act'] is not None:
                raise ValueError('Cannot specify both beat_id and act')
        return v

class SceneGenerationTrackerBase(BaseModel):
    script_id: UUID4
    beat_id: Optional[UUID4] = None
    act: Optional[ActEnum] = None
    status: SceneGenerationStatus
    attempt_count: int = Field(default=1, ge=1)

class SceneGenerationTrackerCreate(SceneGenerationTrackerBase):
    pass

class SceneGenerationTracker(SceneGenerationTrackerBase):
    id: UUID4
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Response Models
class SceneGenerationResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

class SceneListResponse(BaseModel):
    scenes: List[Scene]
    total_count: int
    
class SceneReorderRequest(BaseModel):
    scene_id: UUID4
    new_position: float = Field(..., ge=0)
    beat_id: UUID4  # To validate scene belongs to beat

class BatchSceneCreateRequest(BaseModel):
    beat_id: UUID4
    scenes: List[SceneCreate]

class BeatSceneGenerationRequest(BaseModel):
    beat_id: UUID4
    script_id: UUID4

class ActSceneGenerationRequest(BaseModel):
    act: ActEnum
    script_id: UUID4

class DialogueBlock(BaseModel):
    character_name: str
    dialogue: str
    parenthetical: str | None = None
    position: int

class GeneratedScene(BaseModel):
    scene_heading: str
    scene_description: str
    dialogue_blocks: List[DialogueBlock] | None = None
    estimated_duration: float

class SceneResponse(BaseModel):
    id: UUID4
    beat_id: UUID4
    position: float
    scene_heading: str
    scene_description: str
    dialogue_blocks: Optional[List[DialogueBlock]] = None
    estimated_duration: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SceneGenerationResult(BaseModel):
    beat_id: UUID4
    scenes: List[SceneResponse]
    source: str

    class Config:
        from_attributes = True

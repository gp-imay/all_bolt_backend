# app/schemas/scene_segment.py
from pydantic import BaseModel, UUID4, Field, validator
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum


class ComponentType(str, Enum):
    HEADING = "HEADING"
    ACTION = "ACTION"
    DIALOGUE = "DIALOGUE"
    CHARACTER = "CHARACTER"
    TRANSITION = "TRANSITION"

# Base models for components
class ComponentBase(BaseModel):
    component_type: ComponentType
    position: float = Field(..., description="Position of this component within the segment")
    content: str = Field(..., min_length=1, description="Text content of the component")
    character_name: Optional[str] = Field(None, description="Character name for DIALOGUE components")
    parenthetical: Optional[str] = Field(None, description="Parenthetical direction for DIALOGUE components")
    
    # Validator to ensure character_name is provided for DIALOGUE components
    @validator('character_name')
    def validate_character_name(cls, v, values):
        if values.get('component_type') == ComponentType.DIALOGUE and not v:
            raise ValueError('character_name is required for DIALOGUE components')
        return v


class ComponentCreate(ComponentBase):
    id: UUID4
    pass
    class Config:
        from_attributes = True


class Component(ComponentBase):
    id: UUID4
    scene_segment_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Base models for segments
class SceneSegmentBase(BaseModel):
    segment_number: float = Field(..., description="Position of this segment within the script")
    script_id: UUID4


class SceneSegmentCreate(SceneSegmentBase):
    beat_id: Optional[UUID4] = None
    scene_description_id: Optional[UUID4] = None
    components: List[ComponentCreate] = Field(..., min_items=1, description="Components that make up this segment")


class SceneSegmentUpdate(BaseModel):
    segment_number: Optional[float] = None
    beat_id: Optional[UUID4] = None
    scene_description_id: Optional[UUID4] = None


class SceneSegment(SceneSegmentBase):
    id: UUID4
    beat_id: Optional[UUID4] = None
    scene_description_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    components: List[Component] = []

    class Config:
        from_attributes = True


# Additional schemas for specialized operations
class ComponentUpdate(BaseModel):
    position: Optional[float] = None
    content: Optional[str] = None
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None


class ReorderComponentRequest(BaseModel):
    component_id: UUID4
    new_position: float


class ReorderSegmentRequest(BaseModel):
    segment_id: UUID4
    new_segment_number: float


class BulkCreateSegmentsRequest(BaseModel):
    script_id: UUID4
    beat_id: Optional[UUID4] = None
    scene_description_id: Optional[UUID4] = None
    segments: List[SceneSegmentCreate]


class SegmentListResponse(BaseModel):
    segments: List[SceneSegment]
    total: int
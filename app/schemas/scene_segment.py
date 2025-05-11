# app/schemas/scene_segment.py
from pydantic import BaseModel, UUID4, Field, validator
from typing import List, Optional, Dict, Any
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
    content: str = Field(..., description="Text content of the component")
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


#### For Script Edits

### Writing the below component type class for just FE integration
### FE sends parenthetical as one of component type so it is expected to accept parenthetical in request body
class ComponentTypeFE(str, Enum):
    HEADING = "HEADING"
    ACTION = "ACTION"
    DIALOGUE = "DIALOGUE"
    CHARACTER = "CHARACTER"
    TRANSITION = "TRANSITION"
    PARENTHETICAL = "PARENTHETICAL"

class ComponentChange(BaseModel):
    id: UUID4
    component_type: ComponentTypeFE
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None

class NewComponentForSegment(BaseModel):
    """A new component to be created within a new segment"""
    component_type: ComponentTypeFE
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    frontendId  : str = Field(..., description="Temporary frontend ID for the component")

class NewSegment(BaseModel):
    """A new segment to be created with its components"""
    segmentNumber: float
    beatId: Optional[str] = None
    sceneDescriptionId: Optional[str] = None
    frontendId: str = Field(..., description="Temporary frontend ID for the segment")
    components: List[NewComponentForSegment] = []

class NewComponentForExistingSegment(BaseModel):
    """A new component to be added to an existing segment"""
    segment_id: str
    component_type: ComponentType
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    frontendId: str = Field(..., description="Temporary frontend ID for the component")

class ScriptChangesRequest(BaseModel):
    """
    Comprehensive payload for syncing script changes in a single transaction.
    Supports both FROM_SCRATCH and WITH_AI creation methods.
    """
    # Existing components that were modified (by segment)
    changedSegments: Dict[str, List[ComponentChange]] = {}
    
    # IDs of elements and segments to delete
    deletedElements: List[str] = []
    deletedSegments: List[str] = []
    
    # New segments with their components
    newSegments: List[NewSegment] = []
    
    # New components to add to existing segments
    newComponentsInExistingSegments: List[NewComponentForExistingSegment] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "changedSegments": {
                    "123e4567-e89b-12d3-a456-426614174000": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174001",
                            "component_type": "DIALOGUE",
                            "position": 1000.0,
                            "content": "Updated dialogue text",
                            "character_name": "JOHN"
                        }
                    ]
                },
                "deletedElements": ["123e4567-e89b-12d3-a456-426614174002"],
                "deletedSegments": ["123e4567-e89b-12d3-a456-426614174003"],
                "newSegments": [
                    {
                        "segmentNumber": 5000.0,
                        "beatId": "123e4567-e89b-12d3-a456-426614174004",
                        "sceneDescriptionId": "123e4567-e89b-12d3-a456-426614174005",
                        "frontendId": "temp-seg-abc123",
                        "components": [
                            {
                                "component_type": "HEADING",
                                "position": 1000.0,
                                "content": "INT. LIVING ROOM - DAY",
                                "frontendId": "temp-el-xyz789"
                            },
                            {
                                "component_type": "ACTION",
                                "position": 2000.0,
                                "content": "John enters the room, looking tired.",
                                "frontendId": "temp-el-def456"
                            }
                        ]
                    }
                ],
                "newComponentsInExistingSegments": [
                    {
                        "segment_id": "123e4567-e89b-12d3-a456-426614174006",
                        "component_type": "DIALOGUE",
                        "position": 3000.0,
                        "content": "I can't believe this happened.",
                        "character_name": "JANE",
                        "frontendId": "temp-el-ghi789"
                    }
                ]
            }
        }



class IdMappings(BaseModel):
    """Mapping of frontend temporary IDs to backend-generated UUIDs"""
    segments: Dict[str, str] = Field(default_factory=dict, description="Maps frontend segment IDs to backend UUIDs")
    components: Dict[str, str] = Field(default_factory=dict, description="Maps frontend component IDs to backend UUIDs")

class ScriptChangesResponse(BaseModel):
    """
    Response from the script changes endpoint with detailed counts
    of the operations performed and ID mappings for new elements.
    """
    success: bool
    message: str
    updated_components: int
    deleted_components: int
    deleted_segments: int
    created_segments: int = 0
    created_components: int = 0
    idMappings: IdMappings = Field(default_factory=IdMappings)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Script changes applied successfully",
                "updated_components": 2,
                "deleted_components": 1,
                "deleted_segments": 0,
                "created_segments": 1,
                "created_components": 3,
                "idMappings": {
                    "segments": {
                        "temp-seg-abc123": "550e8400-e29b-41d4-a716-446655440000"
                    },
                    "components": {
                        "temp-el-xyz789": "550e8400-e29b-41d4-a716-446655440001",
                        "temp-el-def456": "550e8400-e29b-41d4-a716-446655440002",
                        "temp-el-ghi789": "550e8400-e29b-41d4-a716-446655440003"
                    }
                }
            }
        }
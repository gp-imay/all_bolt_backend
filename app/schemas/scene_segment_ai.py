# app/schemas/scene_segment_ai.py

from pydantic import BaseModel, UUID4, Field
from typing import List, Optional, Dict, Any
from enum import Enum

from app.schemas.scene_segment import ComponentType  # Import existing enum

class ScriptSceneGenerationRequestUser(BaseModel):
    script_id: UUID4


class SceneSegmentGenerationRequest(BaseModel):
    script_id: UUID4
    scene_description_id: UUID4
    story_synopsis: str
    genre: str
    arc_structure: str
    beat_position: int
    template_beat_title: str
    template_beat_definition: str
    story_specific_beat_title: str
    story_specific_beat_description: str
    scene_title: str  # Scene heading
    scene_description: str
    min_word_count: Optional[int] = 200
    previous_scenes: Optional[List[str]] = None

class ComponentTypeAI(str, Enum):
    HEADING = "HEADING"
    ACTION = "ACTION"
    DIALOGUE = "DIALOGUE"
    CHARACTER = "CHARACTER"
    TRANSITION = "TRANSITION"

class AISceneComponent(BaseModel):
    component_type: ComponentTypeAI
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    # component_id : UUID4

class GeneratedSceneSegment(BaseModel):
    components: List[AISceneComponent]


class AISceneComponentResponse(BaseModel):
    component_type: ComponentTypeAI
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    component_id : UUID4

class GeneratedSceneSegmentResponseResponse(BaseModel):
    components: List[AISceneComponentResponse]

class AISceneSegmentGenerationResponse(BaseModel):
    success: bool
    input_context: Optional[Dict[str, Any]] = None
    generated_segment: Optional[GeneratedSceneSegmentResponseResponse] = None
    fountain_text: Optional[str] = None
    error: Optional[str] = None
    scene_segment_id: Optional[UUID4] = None
    creation_method: str
    message: str

class AISceneGenerationResponse(BaseModel):
    success: bool
    input_context: Optional[dict] = None
    generated_segment: Optional[GeneratedSceneSegment] = None
    fountain_text: Optional[str] = None
    error: Optional[str] = None

class SceneSegmentGenerationResponse(BaseModel):
    success: bool
    input_context: Optional[Dict[str, Any]] = None
    generated_segment: Optional[GeneratedSceneSegment] = None
    fountain_text: Optional[str] = None
    error: Optional[str] = None
    scene_segment_id: Optional[UUID4] = None
    creation_method: str
    message: str

class ComponentCreate(BaseModel):
    component_type: ComponentTypeAI
    position: float
    content: str
    character_name: Optional[str] = None
    parenthetical: Optional[str] = None
    # id : UUID4
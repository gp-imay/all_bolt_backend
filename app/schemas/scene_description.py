# schemas/scene.py
from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from schemas.scene import ActEnum

class SceneBase(BaseModel):
    scene_heading: str = Field(..., min_length=1, max_length=255)
    scene_description: str = Field(..., min_length=1)

class SceneCreate(SceneBase):
    beat_id: UUID4
    position: Optional[int] = None

class SceneUpdate(BaseModel):
    scene_heading: Optional[str] = Field(None, min_length=1, max_length=255)
    scene_description: Optional[str] = None
    position: Optional[int] = None

class Scene(SceneBase):
    id: UUID4
    beat_id: UUID4
    position: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SceneGenerationRequest(BaseModel):
    beat_id: UUID4

class SceneGenerationResponse(BaseModel):
    scenes: List[Scene]
    message: str = "Scenes generated successfully"

# For OpenAI response
class GeneratedScene(BaseModel):
    scene_heading: str
    scene_description: str

class BeatSceneDescriptionGenerationRequest(BaseModel):
    beat_id: UUID4

class SceneDescriptionResponse(BaseModel):
    id: UUID4
    beat_id: UUID4
    position: int
    scene_heading: str
    scene_description: str
    scene_detail_for_ui: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SceneDescriptionCreate(BaseModel):
    beat_id: UUID4
    position: int
    scene_heading: str = Field(..., min_length=1, max_length=1000)
    scene_description: str = Field(..., min_length=1)


class SceneDescriptionResult(BaseModel):
    beat_id: UUID4
    scenes: List[SceneDescriptionResponse]
    source: str = "generated"

    class Config:
        from_attributes = True


class GeneratedSceneResponse(BaseModel):
    id: UUID4
    beat_id: UUID4
    position: int
    scene_heading: str
    scene_description: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class TemplateBeat(BaseModel):
    name: str
    position: int
    description: str
    number_of_scenes: int

class Context(BaseModel):
    script_title: str
    genre: str
    beat_position: int
    template_beat: TemplateBeat
    source: str
    num_scenes: Optional[int] = None

class SceneDescriptionResponsePost(BaseModel):
    success: bool
    context: Context
    generated_scenes: List[GeneratedSceneResponse]

    class Config:
        from_attributes = True


class SceneDescriptionPatchRequest(BaseModel):
    scene_detail_for_ui: str = Field(..., description="Updated scene detail in format 'Scene Title: {heading} : {description}'")

class SceneDescriptionPatch(BaseModel):
    scene_heading: Optional[str] = None
    scene_description: Optional[str] = None

class ActSceneDescriptionGenerationRequest(BaseModel):
    script_id: UUID4
    act: ActEnum



class ContextAct(BaseModel):
    script_title: str
    genre: str
    beat_position: int
    template_beat: TemplateBeat
    source: str
    num_scenes: Optional[int] = None

class ActSceneDescriptionResult(BaseModel):
    success: bool
    context: ContextAct
    context: Dict[str, Any]
    generated_scenes: List[SceneDescriptionResponse]

    class Config:
        from_attributes = True

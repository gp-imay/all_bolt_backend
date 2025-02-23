# schemas/scene.py
from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime

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
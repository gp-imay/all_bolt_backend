from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.user import User
from app.schemas.scene import (
    Scene,
    SceneCreate,
    SceneGenerationResponse,
    GeneratedScene,
    BeatSceneGenerationRequest,
    ActSceneGenerationRequest,
    SceneGenerationRequest,
    SceneGenerationResult
)
from app.services.scene_service import SceneService, SceneGenerationService
from app.services.openai_service import AzureOpenAIService
from app.models.beats import Beat, ActEnum

router = APIRouter()

@router.post("/beat", response_model=SceneGenerationResult)
async def generate_scenes_for_beat(
    request: BeatSceneGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate scenes for a specific beat.
    """
    scene_generator = SceneGenerationService()
    try:
        # Create generation request
        generation_request = SceneGenerationRequest(
            script_id=request.script_id,
            beat_id=request.beat_id
        )
        
        # Use the service to handle generation
        result = await scene_generator.generate_scenes(db, generation_request)
        
        return result

    except Exception as e:
        return SceneGenerationResponse(
            status="error",
            message="Scene generation failed",
            error={"detail": str(e)}
        )

@router.post("/act", response_model=SceneGenerationResponse)
async def generate_scenes_for_act(
    request: ActSceneGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate scenes for all beats in an act.
    """
    scene_generator = SceneGenerationService()
    try:
        # Create generation request
        generation_request = SceneGenerationRequest(
            script_id=request.script_id,
            act=request.act
        )
        
        # Use the service to handle generation
        result = await scene_generator.generate_scenes(db, generation_request)
        
        return SceneGenerationResponse(
            status="success",
            message=f"Scenes generated for all beats in {request.act}",
            data=result
        )

    except Exception as e:
        return SceneGenerationResponse(
            status="error",
            message="Act scene generation failed",
            error={"detail": str(e)}
        )
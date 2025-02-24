# app/routers/scene_descriptions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from auth.dependencies import get_current_user
from schemas.user import User
from schemas.scene_description import (
    SceneDescriptionResponse,
    BeatSceneDescriptionGenerationRequest,
    SceneDescriptionResult,
    SceneDescriptionResponsePost,
    SceneDescriptionPatchRequest
)
from services.scene_description_service import SceneDescriptionService

router = APIRouter()

# @router.post("/beat", response_model=SceneDescriptionResult)
@router.post("/beat")
async def generate_scene_descriptions_for_beat(
    request: BeatSceneDescriptionGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate scene descriptions for a specific beat and store them in the database.
    """
    scene_service = SceneDescriptionService()
    try:
        result = await scene_service.generate_scene_description_for_beat(
            db=db,
            beat_id=request.beat_id,
            user_id=current_user.id
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scene descriptions: {str(e)}"
        )

@router.get("/beat/{beat_id}", response_model=List[SceneDescriptionResponse])
async def get_scene_descriptions_for_beat_api(
    beat_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all scene descriptions for a specific beat.
    """
    scene_service = SceneDescriptionService()
    try:
        return scene_service.get_scene_descriptions_for_beat(
            db=db,
            beat_id=beat_id,
            user_id=current_user.id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scene descriptions: {str(e)}"
        )
    
@router.patch("/{scene_id}", response_model=SceneDescriptionResponse)
async def update_scene_description(
    scene_id: UUID,
    scene_update: SceneDescriptionPatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a scene description based on edited UI string.
    Expects scene_detail_for_ui in format: 'Scene Title: {heading} : {description}'
    """
    scene_service = SceneDescriptionService()
    return await scene_service.update_scene_description(
        db=db,
        scene_id=scene_id,
        user_id=current_user.id,
        scene_detail=scene_update.scene_detail_for_ui
    )

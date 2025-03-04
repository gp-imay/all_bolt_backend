# app/routers/scene_segments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import logging

from database import get_db
from auth.dependencies import get_current_user
from schemas.user import User
from schemas.scene_segment import (
    SceneSegment,
    SceneSegmentCreate,
    SceneSegmentUpdate,
    Component,
    ComponentCreate,
    ComponentUpdate,
    ReorderComponentRequest,
    ReorderSegmentRequest,
    BulkCreateSegmentsRequest,
    SegmentListResponse
)
from services.scene_segment_service import SceneSegmentService

from services.scene_segment_ai_service import SceneSegmentAIService
from schemas.scene_segment_ai import SceneSegmentGenerationResponse, ScriptSceneGenerationRequestUser


from models import scene_segments

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=SceneSegment, status_code=status.HTTP_201_CREATED)
async def create_scene_segment(
    scene_segment: SceneSegmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new scene segment with initial components.
    """
    return SceneSegmentService.create_scene_segment(db, scene_segment)

@router.get("/{segment_id}", response_model=SceneSegment)
async def get_scene_segment(
    segment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific scene segment by ID.
    """
    return SceneSegmentService.get_scene_segment(db, segment_id)

@router.patch("/{segment_id}", response_model=SceneSegment)
async def update_scene_segment(
    segment_id: UUID,
    scene_segment: SceneSegmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a scene segment's metadata (not its components).
    """
    return SceneSegmentService.update_scene_segment(db, segment_id, scene_segment)

@router.delete("/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene_segment(
    segment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a scene segment and all its components.
    """
    SceneSegmentService.delete_scene_segment(db, segment_id)
    return None

@router.post("/reorder", response_model=SceneSegment)
async def reorder_segment(
    reorder_request: ReorderSegmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reorder a scene segment within its script.
    """
    return SceneSegmentService.reorder_scene_segment(
        db, 
        reorder_request.segment_id, 
        reorder_request.new_segment_number
    )

@router.post("/batch", response_model=List[SceneSegment])
async def create_scene_segments_batch(
    batch_request: BulkCreateSegmentsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple scene segments at once.
    Useful for importing or pasting large chunks of content.
    """
    segments = []
    for segment_create in batch_request.segments:
        # Ensure script_id is consistent
        segment_create.script_id = batch_request.script_id
        
        # Apply optional beat/scene description
        if batch_request.beat_id and not segment_create.beat_id:
            segment_create.beat_id = batch_request.beat_id
        if batch_request.scene_description_id and not segment_create.scene_description_id:
            segment_create.scene_description_id = batch_request.scene_description_id
            
        segments.append(SceneSegmentService.create_scene_segment(db, segment_create))
    
    return segments

# Component API endpoints
@router.post("/{segment_id}/components", response_model=Component)
async def add_component(
    segment_id: UUID,
    component: ComponentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new component to a scene segment.
    """
    return SceneSegmentService.add_component(db, segment_id, component)

@router.patch("/components/{component_id}", response_model=Component)
async def update_component(
    component_id: UUID,
    component: ComponentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific component.
    """
    return SceneSegmentService.update_component(db, component_id, component)

@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a component.
    """
    SceneSegmentService.delete_component(db, component_id)
    return None

@router.post("/components/reorder", response_model=Component)
async def reorder_component(
    reorder_request: ReorderComponentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reorder a component within its scene segment.
    """
    return SceneSegmentService.reorder_component(
        db, 
        reorder_request.component_id, 
        reorder_request.new_position
    )

@router.post("/{segment_id}/components/batch", response_model=List[Component])
async def update_components_batch(
    segment_id: UUID,
    components: List[ComponentCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add multiple new components to a scene segment at once.
    """
    result = []
    for component in components:
        result.append(SceneSegmentService.add_component(db, segment_id, component))
    return result

class AutoSaveRequest(BaseModel):
    components: List[dict]  # Flexible structure to handle both new and existing components

@router.post("/{segment_id}/autosave", response_model=List[Component])
async def auto_save_segment(
    segment_id: UUID,
    request: AutoSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Efficiently update multiple components at once for auto-save.
    Can handle updates to existing components and creation of new ones.
    """
    return SceneSegmentService.batch_update_components(db, segment_id, request.components)

@router.get("/script/{script_id}", response_model=SegmentListResponse)
async def get_segments_for_script(
    script_id: UUID,
    skip: int = 0,
    limit: int = 100,
    beat_id: Optional[UUID] = None,
    scene_description_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all scene segments for a specific script.
    Supports optional filtering by beat_id or scene_description_id.
    """
    segments, total = SceneSegmentService.get_scene_segments_for_script(
        db, 
        script_id, 
        skip=skip, 
        limit=limit,
        beat_id=beat_id,
        scene_description_id=scene_description_id
    )
    
    return SegmentListResponse(segments=segments, total=total)

class TextToSegmentRequest(BaseModel):
    script_id: UUID
    segment_number: float
    text: str
    beat_id: Optional[UUID] = None
    scene_description_id: Optional[UUID] = None

@router.post("/from-text", response_model=SceneSegment)
async def create_segment_from_text(
    request: TextToSegmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new scene segment from raw text.
    Automatically detects and creates appropriate components based on the text.
    """
    return SceneSegmentService.create_segment_with_components_from_text(
        db=db,
        script_id=request.script_id,
        segment_number=request.segment_number,
        text=request.text,
        beat_id=request.beat_id,
        scene_description_id=request.scene_description_id
    )

@router.get("/script/{script_id}/next-segment-number", response_model=float)
async def get_next_segment_number(
    script_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next available segment number for a script.
    Useful when creating new segments to ensure proper ordering.
    """
    # Query for the highest segment number
    result = SceneSegmentService.fetch_next_segment_number(db=db, script_id=script_id)
    # If no segments exist, start at 1000
    if result is None:
        return 1000.0
    
    # Otherwise, add 1000 to the highest segment number
    return result + 1000.0

@router.get("/{segment_id}/next-component-position", response_model=float)
async def get_next_component_position(
    segment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next available position for a component within a segment.
    Useful when adding new components to ensure proper ordering.
    """
    try:
        return SceneSegmentService.get_next_component_position(db, segment_id)
    except HTTPException as e:
        # Re-raise the exception to maintain the status code and detail
        raise
    except Exception as e:
        # Log unexpected errors and return a 500 error
        logger.error(f"Unexpected error getting next component position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving next component position: {str(e)}"
        )

@router.get("/script/{script_id}/export", response_model=str)
async def export_screenplay(
    script_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export the screenplay as formatted text.
    """
    return SceneSegmentService.export_screenplay_text(db, script_id)

@router.post("/components/{component_id}/auto-format", response_model=Component)
async def auto_format_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Automatically apply formatting corrections to a component based on screenplay conventions.
    """
    return SceneSegmentService.auto_format_component(db, component_id)

@router.post("/ai/generate-next", response_model=SceneSegmentGenerationResponse)
async def generate_next_segment(
    request: ScriptSceneGenerationRequestUser,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a scene segment for the next available scene without a segment.
    The system automatically finds the next scene description without a segment
    and generates content for it.
    """
    ai_service = SceneSegmentAIService()
    return await ai_service.generate_next_segment(
        db=db,
        script_id=request.script_id,
        user_id=current_user.id
    )

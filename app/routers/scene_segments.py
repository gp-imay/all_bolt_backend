# app/routers/scene_segments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.user import User
from app.schemas.scene_segment import (
    SceneSegment,
    SceneSegmentCreate,
    SceneSegmentUpdate,
    Component,
    ComponentCreate,
    ComponentUpdate,
    ReorderComponentRequest,
    ReorderSegmentRequest,
    BulkCreateSegmentsRequest,
    SegmentListResponse,
    ScriptChangesResponse,
    ScriptChangesRequest
)
from app.services.scene_segment_service import SceneSegmentService
from app.services.script_service import ScriptService

from app.services.scene_segment_ai_service import SceneSegmentAIService
from app.schemas.scene_segment_ai import (SceneSegmentGenerationResponse, 
                                          ScriptSceneGenerationRequestUser, 
                                          AISceneSegmentGenerationResponse,
                                          ShortenComponentResponse, ApplyShortenedTextRequest, ApplyShortenedTextResponse,
                                          RewriteComponentResponse, ApplyRewriteTextResponse, ApplyRewriteTextRequest,
                                          ApplyExpandedTextRequest, ApplyExpandedTextResponse, ExpandComponentResponse,
                                          ApplyContinuationRequest, ApplyContinuationResponse, ContinueComponentResponse,
                                          ApplyTransformRequest
                                          )
from app.models.script import ScriptCreationMethod
from app.models import scene_segments

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

@router.post("/ai/generate-next", response_model=AISceneSegmentGenerationResponse)
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


@router.post("/ai/get-or-generate-first", response_model=AISceneSegmentGenerationResponse)
async def get_or_generate_first_segment(
    request: ScriptSceneGenerationRequestUser,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the first scene segment for a script or generate it if it doesn't exist.
    
    This endpoint first checks if a scene segment already exists for the script.
    If one exists, it returns the first segment. If no segment exists, it uses
    AI to generate the first segment and returns it.
    """
    ai_service = SceneSegmentAIService()
    return await ai_service.get_or_generate_first_segment(
        db=db,
        script_id=request.script_id,
        user_id=current_user.id
    )


@router.put("/{script_id}/changes_old", response_model=ScriptChangesResponse)
async def update_script_changes_old(
    script_id: UUID,
    changes: ScriptChangesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply multiple changes to script segments and components in a single operation.
    """
    # Verify script exists and belongs to user
    existing_script = ScriptService.get_script(db=db, script_id=script_id)
    if existing_script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this script"
        )
    
    # Process the changes
    result = SceneSegmentService.apply_script_changes(
        db=db,
        script_id=script_id,
        changed_segments=changes.changedSegments,
        deleted_elements=changes.deletedElements,
        deleted_segments=changes.deletedSegments
    )
    
    return result

@router.put("/{script_id}/changes", response_model=ScriptChangesResponse)
async def update_script_changes(
    script_id: UUID,
    changes: ScriptChangesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply multiple changes to script segments and components in a single operation.
    
    This endpoint handles:
    - Updates to existing components
    - Deletion of components and segments
    - Creation of new segments with components
    - Addition of new components to existing segments
    
    All changes are processed in a single transaction for consistency.
    """
    # Verify script exists and belongs to user
    existing_script = ScriptService.get_script(db=db, script_id=script_id)
    if existing_script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this script"
        )
    
    # Process the changes
    result = SceneSegmentService.apply_script_changes(
        db=db,
        script_id=script_id,
        changed_segments=changes.changedSegments,
        deleted_elements=changes.deletedElements,
        deleted_segments=changes.deletedSegments,
        new_segments=changes.newSegments,
        new_components_in_existing_segments=changes.newComponentsInExistingSegments
    )
    
    # Update script progress if needed
    if existing_script.creation_method in [ScriptCreationMethod.FROM_SCRATCH, ScriptCreationMethod.WITH_AI]:
        # Calculate progress based on the number of segments, components, etc.
        # This is a simplified example - you may want to develop a more sophisticated algorithm
        total_segments = db.query(scene_segments.SceneSegment).filter(
            scene_segments.SceneSegment.script_id == script_id,
            scene_segments.SceneSegment.is_deleted.is_(False)
        ).count()
        
        if total_segments > 0:
            # Update progress (assuming more segments = more progress)
            progress = min(int(total_segments * 5), 100)  # Cap at 100%
            existing_script.script_progress = progress
            db.commit()
    
    return result


@router.post("/components/{component_id}/shorten", response_model=ShortenComponentResponse)
async def shorten_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate multiple shortened alternatives for a component's content using AI.
    Works for both ACTION and DIALOGUE components.
    """
    return SceneSegmentAIService.shorten_component(db, component_id)


@router.post("/components/{component_id}/apply-shortened", response_model=ApplyShortenedTextResponse)
async def apply_shortened_text(
    component_id: UUID,
    request: ApplyShortenedTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply a selected themed shortened text to the component.
    Records the selection for analytics and tracking purposes.
    """
    # Call the service method to handle the business logic
    ai_service = SceneSegmentAIService()
    return ai_service.apply_shortening_alternative(
        db=db,
        component_id=component_id,
        alternative_text=request.shortened_text,
        user_id=current_user.id
    )


@router.post("/components/{component_id}/rewrite", response_model=RewriteComponentResponse)
async def rewrite_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate multiple rewritten alternatives for a component's content using AI.
    Works for both ACTION and DIALOGUE components.
    
    Each alternative has a different thematic style (concise, dramatic, minimal, poetic, humorous)
    while maintaining the essential meaning of the original text.
    
    Returns:
        RewriteComponentResponse: Original text and themed alternatives with explanations
    """
    return SceneSegmentAIService.rewrite_component(db, component_id)


@router.post("/components/{component_id}/apply-rewrite", response_model=ApplyRewriteTextResponse)
async def apply_rewrite_text(
    component_id: UUID,
    request: ApplyRewriteTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply a selected rewritten text to the component.
    Records the selection for analytics and tracking purposes.
    
    Args:
        component_id: The ID of the component to update
        request: Contains the selected rewritten text to apply
        
    Returns:
        ApplyRewriteTextResponse: Status of the update operation with the updated component
    """
    # Call the service method to handle the business logic
    ai_service = SceneSegmentAIService()
    return ai_service.apply_rewrite_alternative(
        db=db,
        component_id=component_id,
        rewritten_text=request.rewritten_text,
        user_id=current_user.id
    )


@router.post("/components/{component_id}/expand", response_model=ExpandComponentResponse)
async def expand_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate multiple expanded alternatives for a component's content using AI.
    Works for both ACTION and DIALOGUE components.
    """
    return SceneSegmentAIService.expand_component(db, component_id)


@router.post("/components/{component_id}/apply-expanded", response_model=ApplyExpandedTextResponse)
async def apply_expanded_text(
    component_id: UUID,
    request: ApplyExpandedTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply a selected expanded text to the component.
    Records the selection for analytics and tracking purposes.
    """
    # Call the service method to handle the business logic
    ai_service = SceneSegmentAIService()
    return ai_service.apply_expansion_alternative(
        db=db,
        component_id=component_id,
        expanded_text=request.expanded_text,
        user_id=current_user.id
    )

@router.post("/components/{component_id}/continue", response_model=ContinueComponentResponse)
async def continue_component(
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate multiple AI-assisted continuations for a component's content.
    Works for both ACTION and DIALOGUE components.
    
    Each alternative has a different thematic style (concise, dramatic, minimal, poetic, humorous)
    while maintaining the essential meaning and flow from the original text.
    
    Returns:
        ContinueComponentResponse: Original text and themed continuation alternatives with explanations
    """
    return SceneSegmentAIService.continue_component(db, component_id)


@router.post("/components/{component_id}/apply-continuation", response_model=ApplyContinuationResponse)
async def apply_continuation(
    component_id: UUID,
    request: ApplyContinuationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply a selected continuation to a component, appending it to the existing content.
    Records the selection for analytics and tracking purposes.
    
    Args:
        component_id: The ID of the component to update
        request: Contains the selected continuation text to apply
        
    Returns:
        ApplyContinuationResponse: Status of the update operation with the updated component
    """
    # Call the service method to handle the business logic
    ai_service = SceneSegmentAIService()
    return ai_service.apply_continuation_alternative(
        db=db,
        component_id=component_id,
        continuation_text=request.continuation_text,
        user_id=current_user.id
    )

@router.post("/components/{component_id}/apply-transform")
async def apply_transform(
    component_id: UUID,
    request: ApplyTransformRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unified endpoint for applying a selected transformation to a component.
    Records the selection in the appropriate history table.
    """
    result = SceneSegmentAIService.apply_transformation(
        db=db,
        component_id=component_id,
        transform_type=request.transform_type,
        alternative_text=request.alternative_text,
        user_id=current_user.id
    )
    
    # For backward compatibility, ensure consistent response structure
    if "component" in result:
        return {
            "component": result["component"],
            "was_updated": result.get("was_updated", True),
            "was_recorded": result.get("was_recorded", True),
            "message": result.get("message", "Transformation applied successfully")
        }
    return result
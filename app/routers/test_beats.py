import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from database import get_db
from services.openai_service import AzureOpenAIService
from services.scene_description_service import SceneDescriptionService
from schemas.scene_segment_ai import AISceneComponent, SceneSegmentGenerationRequest, ComponentType
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import traceback
import logging
from pydantic import BaseModel, UUID4

logger = logging.getLogger(__name__)

router = APIRouter()

class TestScriptInput(BaseModel):
    title: str
    subtitle: str = ""
    genre: str
    story: str

@router.post("/test-beat-generation")
async def test_beat_generation(
    script_data: TestScriptInput,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to generate beats using Azure OpenAI without saving to database.
    This is for testing purposes only.
    """
    openai_service = AzureOpenAIService()
    
    try:
        beats = openai_service.generate_beat_sheet(
            title=script_data.title,
            subtitle=script_data.subtitle,
            genre=script_data.genre,
            story=script_data.story
        )
        
        return {
            "success": True,
            "script_info": script_data.model_dump(),
            "beats": beats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "script_info": script_data.model_dump()
        }
    

@router.post("/test-beat-generation-stream")
async def test_beat_generation_stream(
    script_data: TestScriptInput,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to generate beats using Azure OpenAI with streaming progress.
    Sends incremental updates to the frontend via SSE.
    """
    openai_service = AzureOpenAIService()
    
    try:
        beat_stream = openai_service.generate_beat_sheet_stream(
            title=script_data.title,
            subtitle=script_data.subtitle,
            genre=script_data.genre,
            story=script_data.story
        )
        
        # Wrap the synchronous generator in an async generator for StreamingResponse.
        async def event_generator():
            for partial in beat_stream:
                # Convert each Beat (Pydantic model) to a dict; here, partial is a List[Beat]
                beats_data = [beat.model_dump() for beat in partial]
                # Send a progress update containing the current partial beat sheet
                data = json.dumps({"progress": "update", "beats": beats_data})
                yield f"data: {data}\n\n"
            # Once complete, send a final completion message.
            yield "data: " + json.dumps({"progress": "complete"}) + "\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    except Exception as stream_error:
        # Optionally, you might want to yield an error event
        error_message = str(stream_error)
        logger.error(traceback.format_exc())
        async def error_generator():
            yield "data: " + json.dumps({"progress": "error", "error": str(error_message)}) + "\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")
    

class TestBeatSceneInput(BaseModel):
    beat_title: str
    beat_description: str
    script_genre: str
    tone: Optional[str] = None

@router.post("/test-scene-generation-for-beat")
async def test_scene_generation_for_beat(
    scene_input: TestBeatSceneInput,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to generate scenes for a single beat.
    This is for testing purposes only.
    """
    openai_service = AzureOpenAIService()
    
    try:
        scenes = openai_service.generate_scenes_for_beat(
            beat_title=scene_input.beat_title,
            beat_description=scene_input.beat_description,
            script_genre=scene_input.script_genre,
            tone=scene_input.tone
        )
        
        return {
            "success": True,
            "beat_info": scene_input.model_dump(),
            "generated_scenes": scenes
        }
        
    except Exception as e:
        logger.error(f"Scene generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "beat_info": scene_input.model_dump()
        }

class TestBeatInput(BaseModel):
    title: str
    description: str

class TestActSceneInput(BaseModel):
    act_beats: List[TestBeatInput]  # List of beats with title and description
    script_genre: str
    tone: Optional[str] = None

@router.post("/test-scene-generation-for-act")
async def test_scene_generation_for_act(
    act_input: TestActSceneInput,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to generate scenes for an entire act.
    This is for testing purposes only.
    """
    openai_service = AzureOpenAIService()
    
    try:
        scenes_by_beat = openai_service.generate_scenes_for_act(
            act_beats=act_input.act_beats,
            script_genre=act_input.script_genre,
            tone=act_input.tone
        )
        
        return {
            "success": True,
            "act_info": act_input.model_dump(),
            "scenes_by_beat": scenes_by_beat
        }
        
    except Exception as e:
        logger.error(f"Act scene generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "act_info": act_input.model_dump()
        }

class SceneRegenerationInput(BaseModel):
    scene_id: str
    beat_context: Dict[str, str]
    previous_scene: Optional[Dict[str, str]] = None
    next_scene: Optional[Dict[str, str]] = None
    feedback: Optional[str] = None

@router.post("/test-scene-regeneration")
async def test_scene_regeneration(
    regen_input: SceneRegenerationInput,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to regenerate a specific scene with context.
    This is for testing purposes only.
    """
    openai_service = AzureOpenAIService()
    
    try:
        regenerated_scene = openai_service.regenerate_scene(
            scene_id=regen_input.scene_id,
            beat_context=regen_input.beat_context,
            previous_scene=regen_input.previous_scene,
            next_scene=regen_input.next_scene,
            feedback=regen_input.feedback
        )
        
        return {
            "success": True,
            "input_context": regen_input.model_dump(),
            "regenerated_scene": regenerated_scene
        }
        
    except Exception as e:
        logger.error(f"Scene regeneration failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "input_context": regen_input.model_dump()
        }


class TestSceneGenerationInput(BaseModel):
    beat_id: UUID4
    user_id: UUID4

    class Config:
        json_schema_extra = {
            "example": {
                "beat_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }

@router.post("/test-scene-desc-generation")
async def test_scene_generation(
    input_data: TestSceneGenerationInput,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to generate scenes using Azure OpenAI.
    This endpoint doesn't save the generated scenes to the database.
    """
    scene_service = SceneDescriptionService()
    try:
        result = await scene_service.generate_scene_description_for_beat(
            db=db,
            beat_id=input_data.beat_id,
            user_id=input_data.user_id
        )
        return result
    except HTTPException as e:
        return {
            "success": False,
            "error": str(e.detail),
            "input": input_data.model_dump()}
    
def format_scene_components_to_fountain(components: List[AISceneComponent]) -> str:
    """Helper function to format components as fountain text"""
    fountain_text = ""
    for comp in components:
        if comp.component_type == ComponentType.HEADING:
            fountain_text += f"{comp.content}\n\n"
        elif comp.component_type == ComponentType.ACTION:
            fountain_text += f"{comp.content}\n\n"
        elif comp.component_type == ComponentType.DIALOGUE:
            fountain_text += f"{comp.character_name}\n"
            if comp.parenthetical:
                fountain_text += f"({comp.parenthetical})\n"
            fountain_text += f"{comp.content}\n\n"
        elif comp.component_type == ComponentType.TRANSITION:
            fountain_text += f"{comp.content}\n\n"
    return fountain_text

@router.post("/test-scene-segment-generation")
async def test_scene_segment_generation(
    request: SceneSegmentGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to generate a scene segment from a scene description.
    This is for testing purposes only.
    """
    openai_service = AzureOpenAIService()
    
    try:
        generated_segment = openai_service.generate_scene_segment(
            story_synopsis=request.story_synopsis,
            genre=request.genre,
            arc_structure=request.arc_structure,
            beat_position=request.beat_position,
            template_beat_title=request.template_beat_title,
            template_beat_definition=request.template_beat_definition,
            story_specific_beat_title=request.story_specific_beat_title,
            story_specific_beat_description=request.story_specific_beat_description,
            scene_title=request.scene_title,
            scene_description=request.scene_description,
            min_word_count=request.min_word_count,
            previous_scenes=request.previous_scenes
        )
        
        # Convert to fountain text for display (if needed)
        fountain_text = format_scene_components_to_fountain(generated_segment.components)
        
        return {
            "success": True,
            "input_context": request.model_dump(),
            "generated_segment": generated_segment.model_dump(),
            "fountain_text": fountain_text
        }
        
    except Exception as e:
        logger.error(f"Scene segment generation failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "input_context": request.model_dump()
        }
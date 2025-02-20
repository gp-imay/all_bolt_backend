import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db
from services.openai_service import AzureOpenAIService
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import traceback
import logging

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
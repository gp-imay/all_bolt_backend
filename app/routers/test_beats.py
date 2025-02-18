from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db
from services.openai_service import AzureOpenAIService
from pydantic import BaseModel

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
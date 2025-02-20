# routers/scripts.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from typing import List

from database import get_db
from schemas.script import (
    Script,
    ScriptCreate,
    ScriptUpdate,
    ScriptOut,
    ScriptList,
    ScriptOutForUI
)
from services.script_service import ScriptService
from services.azure_service import AzureStorageService
from services.beat_service import BeatSheetService
from auth.dependencies import get_current_user
from schemas.user import User
from schemas.beat import ScriptWithBeatsResponse, BeatResponse
from schemas.script import ScriptCreationMethod
from models.beats import MasterBeatSheet, Beat


router = APIRouter()

# routers/scripts.py
@router.get("/{script_id}/beatsheet", response_model=List[BeatResponse])
async def get_script_beatsheet(
    script_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    beats = BeatSheetService.get_script_beatsheet(
        db=db,
        script_id=script_id,
        user_id=current_user.id
    )
    print( [
        BeatResponse(
            position=beat.position,
            beat_title=beat.beat_title,
            beat_description=beat.beat_description,
            script_id=beat.script_id,
            beat_act=beat.beat_act,
            beat_id=beat.id
        ) for beat in beats
    ][0])
    
    return [
        BeatResponse(
            position=beat.position,
            beat_title=beat.beat_title,
            beat_description=beat.beat_description,
            script_id=beat.script_id,
            beat_act=beat.beat_act,
            beat_id=beat.id
        ) for beat in beats
    ]
# routers/scripts.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.script import (
    Script,
    ScriptCreate,
    ScriptUpdate,
    ScriptOut,
    ScriptList,
    ScriptOutForUI
)
from app.services.script_service import ScriptService
from app.services.azure_service import AzureStorageService
from app.services.beat_service import BeatSheetService
from app.auth.dependencies import get_current_user
from app.schemas.user import User
from app.schemas.beat import ScriptWithBeatsResponse, BeatResponse, BeatUpdate
from app.schemas.script import ScriptCreationMethod
from app.models.beats import MasterBeatSheet, Beat


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


@router.patch("/{beat_id}", response_model=BeatResponse)
async def update_beat(
    beat_id: UUID,
    beat_update: BeatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific beat's details.
    """
    updated_beat = BeatSheetService.update_beat(
        db=db,
        beat_id=beat_id,
        user_id=current_user.id,
        beat_update=beat_update
    )
    
    return BeatResponse(
        position=updated_beat.position,
        beat_title=updated_beat.beat_title,
        beat_description=updated_beat.beat_description,
        script_id=updated_beat.script_id,
        beat_act=updated_beat.beat_act,
        beat_id=updated_beat.id
    )

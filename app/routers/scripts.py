# app/routers/scripts.py
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
from app.auth.dependencies import get_current_user
from app.schemas.user import User
from app.schemas.beat import ScriptWithBeatsResponse
import time

router = APIRouter()

@router.post("/", response_model=ScriptOut, status_code=status.HTTP_201_CREATED)
async def create_script(
    script: ScriptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new script"""
    return ScriptService.create_script(db=db, script=script, user_id=current_user.id)

@router.get("/", response_model=List[ScriptList])
async def list_scripts(
    skip: int = 0,
    limit: int = 10,
    genre: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all scripts with optional filtering"""
    response = ScriptService.get_scripts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        genre=genre
    )
    response_formatted = []

    for resp in response:
        val = {}
        if not resp.script_progress:
            # script_progress = 0
            val["progress"] = 0
        else:
            val["progress"] = resp.script_progress
        val["id"] = resp.id
        val["name"] = resp.title
        val["genre"] = resp.genre
        val["creation_method"] = resp.creation_method

        val["created_at"] = resp.created_at
        val["user_id"] = resp.user_id
        response_formatted.append(val)
    print("Scripts")
    return response_formatted

@router.get("/{script_id}", response_model=ScriptOut)
async def get_script(
    script_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific script by ID"""
    script = ScriptService.get_script(db=db, script_id=script_id)
    if script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this script"
        )
    return script

@router.put("/{script_id}", response_model=ScriptOut)
async def update_script(
    script_id: UUID,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a script"""
    existing_script = ScriptService.get_script(db=db, script_id=script_id)
    if existing_script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this script"
        )
    return ScriptService.update_script(
        db=db,
        script_id=script_id,
        script_update=script_update
    )

@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a script"""
    existing_script = ScriptService.get_script(db=db, script_id=script_id)
    if existing_script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this script"
        )
    ScriptService.delete_script(db=db, script_id=script_id)

@router.post("/{script_id}/upload", response_model=ScriptOut)
async def upload_script_file(
    script_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a script file to Azure Blob Storage"""
    existing_script = ScriptService.get_script(db=db, script_id=script_id)
    if existing_script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this script"
        )
    
    # Upload file to Azure Blob Storage
    azure_service = AzureStorageService()
    file_url = await azure_service.upload_file(file, script_id)
    
    # Update script with file URL
    script_update = ScriptUpdate(
        is_file_uploaded=True,
        file_url=file_url
    )
    return ScriptService.update_script(
        db=db,
        script_id=script_id,
        script_update=script_update
    )


@router.post("/with-ai", response_model=ScriptWithBeatsResponse)
async def create_script_with_ai(
    script: ScriptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new script with AI-generated beat sheet"""
    return ScriptService.create_script_with_beats(
        db=db, 
        script=script, 
        user_id=current_user.id
    )


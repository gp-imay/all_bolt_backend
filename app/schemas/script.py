# app/schemas/script.py
from pydantic import BaseModel, Field, HttpUrl, UUID4
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from enum import Enum

class ScriptCreationMethod(str, Enum):
    FROM_SCRATCH = "FROM_SCRATCH"
    WITH_AI = "WITH_AI"
    UPLOAD = "UPLOAD"

class ScriptBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Main title of the movie script")
    subtitle: Optional[str] = Field(None, max_length=255, description="Subtitle or tagline of the movie")
    genre: str = Field(..., max_length=100, description="Genre of the movie (free-form)")
    story: str = Field(..., min_length=1, description="Main story or synopsis of the movie")
    creation_method: ScriptCreationMethod = Field(
        default=ScriptCreationMethod.FROM_SCRATCH,
        description="Method used to create the script"
    )




class ScriptBaseForUI(BaseModel):
    name: str
    genre: str
    story: Optional[str] = None
    progress: int = 0  # Default to 0% progress

class ScriptCreate(ScriptBase):
    pass

class ScriptUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    story: Optional[str] = None
    is_file_uploaded: Optional[bool] = None
    file_url: Optional[HttpUrl] = None

class Script(ScriptBase):
    id: UUID4
    user_id: UUID4
    is_file_uploaded: bool = False
    file_url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScriptOut(Script):
    """Script model for API responses with user information"""
    # user_email: str
    pass
    
    class Config:
        from_attributes = True

class ScriptOutForUI(ScriptBaseForUI):
    id: Union[UUID4, str]  # Can be either UUID or string
    created_at: datetime
    user_id: Union[UUID4, str]  # Can be either UUID or string
    
    class Config:
        from_attributes = True

    def dict(self, *args, **kwargs):
        # Convert UUID to string in the output
        data = super().dict(*args, **kwargs)
        if isinstance(data['id'], UUID):
            data['id'] = str(data['id'])
        if isinstance(data['user_id'], UUID):
            data['user_id'] = str(data['user_id'])
        return data

# For listing scripts with minimal information
class ScriptList(BaseModel):
    id: UUID4
    name: str
    genre: str
    progress: int
    created_at: datetime
    user_id: UUID4
    class Config:
        from_attributes = True
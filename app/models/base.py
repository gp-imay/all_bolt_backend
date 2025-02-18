# app/models/base.py
import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class UUIDModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
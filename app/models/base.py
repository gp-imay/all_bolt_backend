# app/models/base.py
import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import  DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class UUIDModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)


class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)

    def soft_delete(self):
        self.deleted_at = func.now()
        self.is_deleted = True

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttachmentBase(BaseModel):
    """Base schema for attachment information"""

    file_name: str
    file_path: str
    file_size: int
    mime_type: str


class AttachmentCreate(AttachmentBase):
    """Schema for creating a new attachment"""

    uploader_id: int
    project_id: Optional[int] = None


class AttachmentUpdate(BaseModel):
    """Schema for updating attachment"""

    file_name: Optional[str] = None


class AttachmentRead(AttachmentBase, BaseSchema):
    """Schema for reading attachment information"""

    id: int
    uploader_id: int
    project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskAttachmentCreate(BaseModel):
    """Schema for creating attachment linked to a task"""

    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: int
    task_id: int

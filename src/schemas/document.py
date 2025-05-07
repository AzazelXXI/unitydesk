from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.document import DocumentType, DocumentPermissionLevel


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Document schemas
class DocumentBase(BaseModel):
    """Base schema for document information"""

    title: str
    description: Optional[str] = None
    document_type: DocumentType
    owner_id: int
    parent_folder_id: Optional[int] = None
    is_starred: bool = False
    is_trashed: bool = False
    content: Optional[str] = None
    is_public: bool = False


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""

    initial_content: Optional[str] = None  # Initial document content


class DocumentUpdate(BaseModel):
    """Schema for updating document information"""

    title: Optional[str] = None
    description: Optional[str] = None
    parent_folder_id: Optional[int] = None
    is_starred: Optional[bool] = None
    is_trashed: Optional[bool] = None
    is_public: Optional[bool] = None


class DocumentReadBasic(DocumentBase, BaseSchema):
    """Basic schema for reading document information"""

    current_version_id: Optional[int] = None
    public_token: Optional[str] = None
    view_count: int = 0
    owner: Dict[str, Any]  # Simplified owner info
    version_count: int = 0


class DocumentRead(DocumentReadBasic):
    """Full schema for reading document information"""

    versions: List[Dict[str, Any]] = []  # Simplified versions
    permissions: List[Dict[str, Any]] = []  # Simplified permissions
    parent_folder: Optional[Dict[str, Any]] = None  # Simplified folder info


# Document version schemas
class DocumentVersionBase(BaseModel):
    """Base schema for document version information"""

    document_id: int
    version_number: int
    content: str
    storage_path: Optional[str] = None
    size_bytes: Optional[int] = None
    created_by_id: int
    change_summary: Optional[str] = None


class DocumentVersionCreate(BaseModel):
    """Schema for creating a new document version"""

    document_id: int
    content: str
    change_summary: Optional[str] = None


class DocumentVersionRead(DocumentVersionBase, BaseSchema):
    """Schema for reading document version information"""

    created_by: Dict[str, Any]  # Simplified creator info
    is_current: bool = False


# Document permission schemas
class DocumentPermissionBase(BaseModel):
    """Base schema for document permission information"""

    document_id: int
    user_id: Optional[int] = None
    permission_level: DocumentPermissionLevel
    is_link: bool = False
    token: Optional[str] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class DocumentPermissionCreate(BaseModel):
    """Schema for creating a document permission"""

    document_id: int
    user_id: Optional[int] = None  # None for link sharing
    permission_level: DocumentPermissionLevel
    is_link: bool = False
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class DocumentPermissionUpdate(BaseModel):
    """Schema for updating document permission"""

    permission_level: Optional[DocumentPermissionLevel] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class DocumentPermissionRead(DocumentPermissionBase, BaseSchema):
    """Schema for reading document permission information"""

    user: Optional[Dict[str, Any]] = None  # Simplified user info if applicable

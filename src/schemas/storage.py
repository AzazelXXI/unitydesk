from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models_backup.storage import StoragePermissionLevel


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# File schemas
class FileBase(BaseModel):
    """Base schema for file information"""

    name: str
    description: Optional[str] = None
    mime_type: str
    size_bytes: int
    storage_path: str
    owner_id: int
    parent_folder_id: Optional[int] = None
    is_starred: bool = False
    is_trashed: bool = False
    checksum: Optional[str] = None


class FileCreate(FileBase):
    """Schema for creating a file record"""

    pass


class FileUpdate(BaseModel):
    """Schema for updating file information"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_starred: Optional[bool] = None
    is_trashed: Optional[bool] = None
    parent_folder_id: Optional[int] = None


class FileRead(FileBase, BaseSchema):
    """Schema for reading file information"""

    trashed_at: Optional[datetime] = None
    view_count: int = 0
    download_count: int = 0
    is_public: bool = False
    public_token: Optional[str] = None
    owner: Dict[str, Any]  # Simplified owner info
    parent_folder: Optional[Dict[str, Any]] = None  # Simplified folder info


# Folder schemas
class FolderBase(BaseModel):
    """Base schema for folder information"""

    name: str
    description: Optional[str] = None
    owner_id: int
    parent_folder_id: Optional[int] = None
    is_starred: bool = False
    is_trashed: bool = False
    is_public: bool = False


class FolderCreate(FolderBase):
    """Schema for creating a new folder"""

    pass


class FolderUpdate(BaseModel):
    """Schema for updating folder information"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_starred: Optional[bool] = None
    is_trashed: Optional[bool] = None
    is_public: Optional[bool] = None
    parent_folder_id: Optional[int] = None


class FolderReadBasic(FolderBase, BaseSchema):
    """Basic schema for reading folder information"""

    trashed_at: Optional[datetime] = None
    owner: Dict[str, Any]  # Simplified owner info


class FolderRead(FolderReadBasic):
    """Full schema for reading folder information"""

    parent_folder: Optional[Dict[str, Any]] = None  # Simplified parent folder info
    file_count: int = 0
    subfolder_count: int = 0
    total_size_bytes: int = 0


# File permission schemas
class FilePermissionBase(BaseModel):
    """Base schema for file permission information"""

    file_id: int
    user_id: Optional[int] = None
    permission_level: StoragePermissionLevel
    is_link: bool = False
    token: Optional[str] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class FilePermissionCreate(BaseModel):
    """Schema for creating a file permission"""

    file_id: int
    user_id: Optional[int] = None  # None for link sharing
    permission_level: StoragePermissionLevel
    is_link: bool = False
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class FilePermissionUpdate(BaseModel):
    """Schema for updating file permission"""

    permission_level: Optional[StoragePermissionLevel] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None


class FilePermissionRead(FilePermissionBase, BaseSchema):
    """Schema for reading file permission information"""

    user: Optional[Dict[str, Any]] = None  # Simplified user info if applicable

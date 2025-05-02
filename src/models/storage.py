from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models.base import RootModel


class StoragePermissionLevel(str, enum.Enum):
    """Permission levels for file/folder sharing"""
    VIEW = "view"          # Can only view
    DOWNLOAD = "download"  # Can view and download
    EDIT = "edit"          # Can edit metadata, upload new versions
    FULL = "full"          # Full control including delete


class File(Base, RootModel):
    """File model for cloud storage"""
    __tablename__ = "files"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(255), nullable=False)  # Path in storage system
    owner_id = Column(Integer, ForeignKey("users.id"))
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    is_starred = Column(Boolean, default=False)
    is_trashed = Column(Boolean, default=False)
    trashed_at = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    checksum = Column(String(255), nullable=True)  # For file integrity checking
    
    # For public sharing
    is_public = Column(Boolean, default=False)
    public_token = Column(String(255), nullable=True, unique=True)
    
    # Relationships
    owner = relationship("User", back_populates="files")
    parent_folder = relationship("Folder", back_populates="files")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")


class Folder(Base, RootModel):
    """Folder model for organizing files"""
    __tablename__ = "folders"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    is_starred = Column(Boolean, default=False)
    is_trashed = Column(Boolean, default=False)
    trashed_at = Column(DateTime, nullable=True)
    is_public = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="folders")
    parent_folder = relationship("Folder", remote_side=[id], backref="subfolders")
    files = relationship("File", back_populates="parent_folder")
    documents = relationship("Document", back_populates="parent_folder")


class FilePermission(Base, RootModel):
    """Permissions for file access"""
    __tablename__ = "file_permissions"
    
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    permission_level = Column(Enum(StoragePermissionLevel), nullable=False)
    
    # For link sharing
    is_link = Column(Boolean, default=False)
    token = Column(String(255), nullable=True, unique=True)
    password = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="permissions")
    user = relationship("User")

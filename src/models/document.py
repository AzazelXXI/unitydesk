from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer
from sqlalchemy.orm import relationship
import enum

from src.database import Base
from src.models.base import BaseModel


class DocumentType(str, enum.Enum):
    """Types of documents"""
    DOCUMENT = "document"  # Text document
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    DRAWING = "drawing"
    FORM = "form"


class DocumentPermissionLevel(str, enum.Enum):
    """Permission levels for document sharing"""
    VIEW = "view"        # Can only view
    COMMENT = "comment"  # Can view and comment
    EDIT = "edit"        # Can edit
    OWNER = "owner"      # Full control


class Document(Base, BaseModel):
    """Document model for collaborative document editing"""
    __tablename__ = "documents"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    is_starred = Column(Boolean, default=False)
    is_trashed = Column(Boolean, default=False)
    content = Column(Text, nullable=True)  # For simple documents or metadata
    current_version_id = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=False)
    public_token = Column(String(255), nullable=True, unique=True)
    view_count = Column(Integer, default=0)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    parent_folder = relationship("Folder", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base, BaseModel):
    """Version history for documents"""
    __tablename__ = "document_versions"
    
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Document content or metadata
    storage_path = Column(String(255), nullable=True)  # Path to stored content
    size_bytes = Column(Integer, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    change_summary = Column(String(255), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User")


class DocumentPermission(Base, BaseModel):
    """Permissions for document access"""
    __tablename__ = "document_permissions"
    
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    permission_level = Column(Enum(DocumentPermissionLevel), nullable=False)
    
    # For link sharing
    is_link = Column(Boolean, default=False)
    token = Column(String(255), nullable=True, unique=True)
    password = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", nullable=True)

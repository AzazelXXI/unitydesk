from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models_backup.messenger import ChatType, MessageType


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Chat schemas
class ChatBase(BaseModel):
    """Base schema for chat information"""

    name: Optional[str] = None  # Can be null for direct chats
    description: Optional[str] = None
    chat_type: ChatType
    is_active: bool = True
    avatar_url: Optional[str] = None
    owner_id: int


class ChatCreate(ChatBase):
    """Schema for creating a new chat"""

    members: List[int] = []  # List of user IDs to add to the chat


class ChatUpdate(BaseModel):
    """Schema for updating chat information"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class ChatMemberBase(BaseModel):
    """Base schema for chat member information"""

    chat_id: int
    user_id: int
    is_admin: bool = False
    nickname: Optional[str] = None
    muted_until: Optional[datetime] = None


class ChatMemberCreate(ChatMemberBase):
    """Schema for adding a member to a chat"""

    pass


class ChatMemberUpdate(BaseModel):
    """Schema for updating chat member information"""

    is_admin: Optional[bool] = None
    nickname: Optional[str] = None
    muted_until: Optional[datetime] = None


class ChatMemberRead(ChatMemberBase, BaseSchema):
    """Schema for reading chat member information"""

    user: Dict[str, Any]  # Simplified user info


class ChatRead(ChatBase, BaseSchema):
    """Schema for reading chat information"""

    members: List[ChatMemberRead] = []
    last_message: Optional[Dict[str, Any]] = None  # Simplified last message


# Message schemas
class MessageBase(BaseModel):
    """Base schema for message information"""

    chat_id: int
    sender_id: Optional[int] = None  # Can be null for system messages
    content: str
    message_type: MessageType = MessageType.TEXT
    parent_id: Optional[int] = None  # For replies
    attachment_url: Optional[str] = None


class MessageCreate(MessageBase):
    """Schema for creating a new message"""

    pass


class MessageUpdate(BaseModel):
    """Schema for updating a message"""

    content: Optional[str] = None
    is_edited: bool = True
    attachment_url: Optional[str] = None


class MessageRead(MessageBase, BaseSchema):
    """Schema for reading message information"""

    is_edited: bool = False
    edited_at: Optional[datetime] = None
    sender: Optional[Dict[str, Any]] = None  # Simplified sender info
    parent_message: Optional[Dict[str, Any]] = None  # Simplified parent message
    replies_count: Optional[int] = None


# Read receipts and reactions could be added later

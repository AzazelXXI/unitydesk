from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, DateTime,Integer
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models_backup.base import RootModel


class ChatType(str, enum.Enum):
    """Types of chat channels"""
    DIRECT = "direct"        # 1-1 chat between two users
    GROUP = "group"          # Group chat for teams or projects
    CHANNEL = "channel"      # Broadcast channel for announcements


class MessageType(str, enum.Enum):
    """Types of messages"""
    TEXT = "text"             # Regular text message
    FILE = "file"             # File attachment
    IMAGE = "image"           # Image attachment
    VIDEO = "video"           # Video attachment
    AUDIO = "audio"           # Audio attachment
    SYSTEM = "system"         # System notification
    CALL = "call"             # Call invitation or summary


class Chat(Base, RootModel):
    """Chat model representing direct messages, group chats, or channels"""
    __tablename__ = "chats"
    
    name = Column(String(255), nullable=True)  # Nullable for direct chats
    description = Column(Text, nullable=True)
    chat_type = Column(Enum(ChatType), nullable=False)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="owned_chats")
    members = relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    
    # For direct chats, we use this helper property to get the other participant
    @property
    def other_member(self, current_user_id):
        """For direct chats, returns the user that is not the current user"""
        if self.chat_type != ChatType.DIRECT:
            return None
        
        for member in self.members:
            if member.user_id != current_user_id:
                return member.user
                
        return None


class ChatMember(Base, RootModel):
    """Association between users and chats"""
    __tablename__ = "chat_members"
    
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_admin = Column(Boolean, default=False)
    nickname = Column(String(100), nullable=True)
    muted_until = Column(DateTime, nullable=True)
    
    # Relationships
    chat = relationship("Chat", back_populates="members")
    user = relationship("User", back_populates="chat_memberships")


class Message(Base, RootModel):
    """Messages sent in chats"""
    __tablename__ = "messages"
    
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    parent_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    attachment_url = Column(String(255), nullable=True)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    parent_message = relationship("Message", remote_side="Message.id", backref="replies")
    
    # Add reactions and read receipts later

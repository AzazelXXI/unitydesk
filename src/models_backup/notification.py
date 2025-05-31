from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models_backup.base import RootModel


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    SYSTEM = "system"  # System-generated notifications
    TASK = "task"      # Task assignments and updates
    MESSAGE = "message" # Chat messages
    MEETING = "meeting" # Meeting invites and reminders
    DOCUMENT = "document" # Document sharing and updates
    PROJECT = "project"  # Project updates
    DEPARTMENT = "department" # Department changes
    MENTION = "mention"  # User mentions


class NotificationChannel(str, enum.Enum):
    """Delivery channels for notifications"""
    IN_APP = "in_app"  # In-app notifications
    EMAIL = "email"    # Email notifications
    PUSH = "push"      # Push notifications for web/mobile
    SMS = "sms"        # SMS notifications


class NotificationPriority(str, enum.Enum):
    """Priority levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base, RootModel):
    """Notification model for user notifications"""
    __tablename__ = "notifications"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    
    # Resource links (what the notification is about)
    resource_type = Column(String(50), nullable=True)  # e.g., "task", "message", "meeting"
    resource_id = Column(Integer, nullable=True)       # ID of the related resource
    
    # Additional data in JSON format (flexible)
    data = Column(JSON, nullable=True)
    
    # Icon for the notification
    icon = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)          # When the user read it
    
    # Action URL (where to go when notification is clicked)
    action_url = Column(String(512), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # Delivery status tracking
    in_app_delivered = Column(Boolean, default=False)
    email_delivered = Column(Boolean, default=False)
    push_delivered = Column(Boolean, default=False)
    sms_delivered = Column(Boolean, default=False)
    

class NotificationSetting(Base, RootModel):
    """User notification preferences per notification type"""
    __tablename__ = "notification_settings"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)
    
    # Minimum priority level to deliver - e.g., "high" means only high/urgent notifications
    min_priority = Column(Enum(NotificationPriority), default=NotificationPriority.LOW)
    
    # Relationships
    user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    __table_args__ = (
        # Composite primary key: combination of user_id and notification_type must be unique
        {"primary_key": (user_id, notification_type)},
    )


class NotificationTemplate(Base, RootModel):
    """Templates for notifications"""
    __tablename__ = "notification_templates"
    
    name = Column(String(100), nullable=False, unique=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    title_template = Column(String(255), nullable=False)
    content_template = Column(Text, nullable=False)
    
    # Optional templates for different channels
    email_subject_template = Column(String(255), nullable=True)
    email_body_template = Column(Text, nullable=True)
    sms_template = Column(String(255), nullable=True)
    
    # Default icon for this template
    default_icon = Column(String(255), nullable=True)
    
    # Is this template active
    is_active = Column(Boolean, default=True)

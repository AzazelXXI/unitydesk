from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models.base import RootModel


class MeetingStatus(str, enum.Enum):
    """Status of a meeting"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Meeting(Base):
    """Meeting model for video conferences"""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    room_name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED)
    description = Column(Text, nullable=True)
    # Adding missing fields from the duplicate class below
    host_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_recurring = Column(Boolean, default=False)
    scheduled_start_time = Column(DateTime, nullable=True)
    scheduled_end_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Relationships
    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan")
    host = relationship("User", foreign_keys=[host_id])


class Participant(Base):
    """Participant model for meeting attendance tracking"""
    __tablename__ = 'participants'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional link to user account
    name = Column(String, nullable=True)  # For guests without accounts
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    is_camera_on = Column(Boolean, default=False)
    is_mic_on = Column(Boolean, default=False)
    is_screen_sharing = Column(Boolean, default=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", foreign_keys=[user_id])

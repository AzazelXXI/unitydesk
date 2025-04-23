from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.meeting import MeetingStatus


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Meeting schemas
class MeetingBase(BaseModel):
    """Base schema for meeting information"""
    room_name: str
    description: Optional[str] = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    host_id: Optional[int] = None
    is_recurring: bool = False
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None


class MeetingCreate(MeetingBase):
    """Schema for creating a new meeting"""
    invited_users: Optional[List[int]] = None  # List of user IDs to invite


class MeetingUpdate(BaseModel):
    """Schema for updating meeting information"""
    room_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MeetingStatus] = None
    host_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None


class MeetingRead(MeetingBase, BaseSchema):
    """Schema for reading meeting information"""
    participant_count: Optional[int] = None
    host: Optional[Dict[str, Any]] = None  # Simplified host info
    is_active: bool = False  # Derived field based on status


# Participant schemas
class ParticipantBase(BaseModel):
    """Base schema for participant information"""
    client_id: str
    meeting_id: int
    user_id: Optional[int] = None  # Optional link to user account
    name: Optional[str] = None  # For guests without accounts
    is_camera_on: bool = False
    is_mic_on: bool = False
    is_screen_sharing: bool = False


class ParticipantCreate(ParticipantBase):
    """Schema for creating a participant record"""
    pass


class ParticipantUpdate(BaseModel):
    """Schema for updating participant information"""
    name: Optional[str] = None
    is_camera_on: Optional[bool] = None
    is_mic_on: Optional[bool] = None
    is_screen_sharing: Optional[bool] = None
    left_at: Optional[datetime] = None


class ParticipantRead(ParticipantBase, BaseSchema):
    """Schema for reading participant information"""
    joined_at: datetime
    left_at: Optional[datetime] = None
    user: Optional[Dict[str, Any]] = None  # Simplified user info if linked
    duration_seconds: Optional[int] = None  # Calculated field


# Meeting invitation schemas
class MeetingInviteCreate(BaseModel):
    """Schema for creating a meeting invitation"""
    meeting_id: int
    user_id: Optional[int] = None
    email: Optional[str] = None  # For external participants
    name: Optional[str] = None  # For external participants
    message: Optional[str] = None

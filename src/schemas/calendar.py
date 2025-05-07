from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.calendar import EventStatus, EventRecurrence, ResponseStatus


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Calendar schemas
class CalendarBase(BaseModel):
    """Base schema for calendar information"""

    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    is_primary: bool = False
    owner_id: int
    is_public: bool = False


class CalendarCreate(CalendarBase):
    """Schema for creating a new calendar"""

    pass


class CalendarUpdate(BaseModel):
    """Schema for updating calendar information"""

    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_primary: Optional[bool] = None
    is_public: Optional[bool] = None


class CalendarRead(CalendarBase, BaseSchema):
    """Schema for reading calendar information"""

    owner: Dict[str, Any]  # Simplified owner info
    event_count: Optional[int] = None


# Event schemas
class EventParticipantBase(BaseModel):
    """Base schema for event participant information"""

    event_id: int
    user_id: int
    response: ResponseStatus = ResponseStatus.NEEDS_ACTION
    is_optional: bool = False
    comment: Optional[str] = None


class EventParticipantCreate(BaseModel):
    """Schema for adding a participant to an event"""

    user_id: int
    is_optional: bool = False


class EventParticipantUpdate(BaseModel):
    """Schema for updating participant information"""

    response: Optional[ResponseStatus] = None
    is_optional: Optional[bool] = None
    comment: Optional[str] = None


class EventParticipantRead(EventParticipantBase, BaseSchema):
    """Schema for reading participant information"""

    user: Dict[str, Any]  # Simplified user info


class EventBase(BaseModel):
    """Base schema for event information"""

    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    virtual_meeting_link: Optional[str] = None
    status: EventStatus = EventStatus.CONFIRMED
    recurrence: EventRecurrence = EventRecurrence.NONE
    recurrence_rule: Optional[str] = None
    all_day: bool = False
    color: Optional[str] = None
    calendar_id: int
    organizer_id: int
    reminder_minutes: Optional[int] = None


class EventCreate(EventBase):
    """Schema for creating a new event"""

    participants: Optional[List[EventParticipantCreate]] = None


class EventUpdate(BaseModel):
    """Schema for updating event information"""

    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    virtual_meeting_link: Optional[str] = None
    status: Optional[EventStatus] = None
    recurrence: Optional[EventRecurrence] = None
    recurrence_rule: Optional[str] = None
    all_day: Optional[bool] = None
    color: Optional[str] = None
    calendar_id: Optional[int] = None
    reminder_minutes: Optional[int] = None


class EventReadBasic(EventBase, BaseSchema):
    """Basic schema for reading event information"""

    organizer: Dict[str, Any]  # Simplified organizer info
    is_past: bool = False


class EventRead(EventReadBasic):
    """Full schema for reading event information"""

    calendar: Dict[str, Any]  # Simplified calendar info
    participants: List[EventParticipantRead] = []


# Calendar sharing schemas
class CalendarShareCreate(BaseModel):
    """Schema for sharing a calendar with a user"""

    user_id: int
    can_edit: bool = False
    can_share: bool = False


class CalendarShareUpdate(BaseModel):
    """Schema for updating calendar sharing permissions"""

    can_edit: Optional[bool] = None
    can_share: Optional[bool] = None

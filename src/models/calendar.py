from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models.base import BaseModel


class EventStatus(str, enum.Enum):
    """Status of an event"""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventRecurrence(str, enum.Enum):
    """Recurrence pattern for events"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"  # Custom recurrence rule


class ResponseStatus(str, enum.Enum):
    """Response status for event participants"""
    ACCEPTED = "accepted"
    TENTATIVE = "tentative"
    DECLINED = "declined"
    NEEDS_ACTION = "needs_action"
    

class Calendar(Base, BaseModel):
    """Calendar model for organizing events"""
    __tablename__ = "calendars"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), nullable=True)  # Color code
    is_primary = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="calendars")
    events = relationship("Event", back_populates="calendar", cascade="all, delete-orphan")


class Event(Base, BaseModel):
    """Event model for calendar entries"""
    __tablename__ = "events"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    virtual_meeting_link = Column(String(255), nullable=True)
    status = Column(Enum(EventStatus), default=EventStatus.CONFIRMED)
    recurrence = Column(Enum(EventRecurrence), default=EventRecurrence.NONE)
    recurrence_rule = Column(String(255), nullable=True)  # iCalendar RRULE format
    all_day = Column(Boolean, default=False)
    color = Column(String(20), nullable=True)  # Override calendar color
    calendar_id = Column(Integer, ForeignKey("calendars.id"))
    organizer_id = Column(Integer, ForeignKey("users.id"))
    reminder_minutes = Column(Integer, nullable=True)  # Minutes before event
    
    # Relationships
    calendar = relationship("Calendar", back_populates="events")
    organizer = relationship("User", back_populates="events")
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")
    
    @property
    def is_past(self):
        """Check if the event is in the past"""
        return datetime.utcnow() > self.end_time


class EventParticipant(Base, BaseModel):
    """Association between users and events"""
    __tablename__ = "event_participants"
    
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    response = Column(Enum(ResponseStatus), default=ResponseStatus.NEEDS_ACTION)
    is_optional = Column(Boolean, default=False)
    comment = Column(Text, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="participants")
    user = relationship("User", back_populates="event_participations")

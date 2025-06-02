import enum
import datetime
import uuid
from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship

from .base import Base


class CalendarViewEnum(str, enum.Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    AGENDA = "Agenda"


class Calendar(Base):
    __tablename__ = "calendars"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color_code = Column(String(7), nullable=True)  # Example: #RRGGBB
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="calendars")
    events = relationship(
        "Event", back_populates="calendar", cascade="all, delete-orphan"
    )

import uuid
import datetime
from sqlalchemy import Column, ForeignKey, String, Text, DateTime, Boolean, UUID
from sqlalchemy.orm import relationship
from .base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    is_recurring = Column(Boolean, default=False)
    color_code = Column(String(7), nullable=True)  # Example: #RRGGBB
    reminder_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Keys
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("calendars.id"), nullable=False)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    calendar = relationship("Calendar", back_populates="events")
    project = relationship("Project", back_populates="events")

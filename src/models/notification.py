import enum
import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SAEnum,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from .base import Base


class NotificationTypeEnum(str, enum.Enum):
    TASK_ASSIGNED = "Task Assigned"
    TASK_COMPLETED = "Task Completed"
    TASK_OVERDUE = "Task Overdue"
    PROJECT_UPDATE = "Project Update"
    MILESTONE_REACHED = "Milestone Reached"
    COMMENT_ADDED = "Comment Added"
    SYSTEM_ALERT = "System Alert"


class Notification(Base):
    """
    Notification model for user notifications
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(
        SAEnum(NotificationTypeEnum, name="notification_type_enum", create_type=False),
        nullable=False,
    )
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )  # Optional link to task
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=True
    )  # Optional link to project

    # Relationships
    user = relationship("User", back_populates="notifications")
    task = relationship("Task")
    project = relationship("Project")

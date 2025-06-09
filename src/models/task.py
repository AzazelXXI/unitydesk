import enum
import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SAEnum,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class TaskStatusEnum(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"


class TaskPriorityEnum(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(TaskStatusEnum, name="task_status_enum", create_type=False),
        nullable=False,
        default=TaskStatusEnum.NOT_STARTED,
    )
    priority = Column(
        SAEnum(TaskPriorityEnum, name="task_priority_enum", create_type=False),
        nullable=False,
        default=TaskPriorityEnum.MEDIUM,
    )
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    tags = Column(String(500), nullable=True)  # JSON string or comma-separated
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationships - Align with Class Diagram
    project = relationship("Project", back_populates="tasks")
    assignees = relationship(
        "User", secondary="task_assignees", back_populates="assigned_tasks"
    )
    comments = relationship(
        "Comment", back_populates="task", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "Attachment", secondary="task_attachments", back_populates="tasks"
    )
    # Task dependencies - a task can depend on other tasks
    dependencies = relationship(
        "Task",
        secondary="task_dependencies",
        primaryjoin="Task.id == task_dependencies.c.task_id",
        secondaryjoin="Task.id == task_dependencies.c.depends_on_task_id",
        back_populates="dependent_tasks",
    )
    dependent_tasks = relationship(
        "Task",
        secondary="task_dependencies",
        primaryjoin="Task.id == task_dependencies.c.depends_on_task_id",
        secondaryjoin="Task.id == task_dependencies.c.task_id",
        back_populates="dependencies",
    )

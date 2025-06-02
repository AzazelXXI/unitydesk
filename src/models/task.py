import enum
import datetime
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SAEnum,
    Text,
    UUID,
)
from sqlalchemy.orm import relationship

from .base import Base
from .association_tables import task_attachment_table


class TaskStatusEnum(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class TaskPriorityEnum(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(TaskStatusEnum, name="task_status_enum", create_type=False),
        nullable=False,
        default=TaskStatusEnum.NOT_STARTED,
    )
    estimated_time = Column(Integer, nullable=True)
    is_recurring = Column(Boolean, nullable=False, default=False)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    priority = Column(
        SAEnum(TaskPriorityEnum, name="task_priority_enum", create_type=False)
    )
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Foreign Key
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationship
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")
    comments = relationship(
        "Comment", back_populates="task", cascade="all, delete-orphan"
    )
    # Many task has many attachment
    attachments = relationship(
        "Attachment", secondary=task_attachment_table, back_populates="tasks"
    )


class Comment(Base):
    """
    This class exist because in the class diagram we use the type of this attribute as a list
    """

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )  # Comment author
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )  # Comment belong to which task

    # Relationship
    author = relationship("User", back_populates="comments")  # Who commented
    task = relationship("Task", back_populates="comments")  # Commented on which task


class Attachment(Base):
    """
    This class exist because in the class diagram we use the type of this attribute as a list
    """

    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationship
    uploader = relationship("User", back_populates="uploaded_attachments")
    # Many attachment has many task
    tasks = relationship(
        "Task", secondary=task_attachment_table, back_populates="attachments"
    )

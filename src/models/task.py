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


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(TaskStatusEnum, name="task_status_enum", create_type=False),
        nullable=False,
        default=TaskStatusEnum.NOT_STARTED,
    )
    estimated_time = Column(Integer, nullable=True)
    is_recurring = Column(Boolean, nullable=True)
    category = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Foreign Key
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Task may created but did not assign
    
    # Relationship
    comments = relationship("Comment", back_populates="task")
    author_comment = relationship("Comment", back_populates="author")
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")

    # Attachment and Comment
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")


class Comment(Base):
    """
    This class exist because in the class diagram we use the type of this attribute as a list
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Comment author
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False) # Comment belong to which task

    # Relationship
    author = relationship("User", back_populates="comments")  # Who commented
    task = relationship("Task", back_populates="comments")  # Commented on which task


class Attachment(Base):
    """
    This class exist because in the class diagram we use the type of this attribute as a list
    """

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Foreign Key
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship
    task = relationship("Task", back_populates="attach")
    uploader = relationship("User", back_populates="upload_attachmets")

from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models.base import RootModel


class TaskStatus(str, enum.Enum):
    """Status of a task"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Priority levels for tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Project(Base, RootModel):
    """Project model for organizing related tasks"""
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(100), default="active")
    color = Column(String(20), nullable=True)  # Color code
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects_owned")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base, RootModel):
    """Task model for managing work items"""
    __tablename__ = "tasks"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    completion_percentage = Column(Integer, default=0)
    creator_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="tasks_created")
    project = relationship("Project", back_populates="tasks")
    assignees = relationship("TaskAssignee", back_populates="task", cascade="all, delete-orphan")
    parent_task = relationship("Task", remote_side="Task.id", backref="subtasks")


class TaskAssignee(Base, RootModel):
    """Association between tasks and users (assignees)"""
    __tablename__ = "task_assignees"
    
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_responsible = Column(Boolean, default=False)  # Main assignee responsible for the task
    
    # Relationships
    task = relationship("Task", back_populates="assignees")
    user = relationship("User", back_populates="task_assignments")


class TaskComment(Base, RootModel):
    """Comments on tasks"""
    __tablename__ = "task_comments"
    
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    
    # Relationships
    task = relationship("Task", backref="comments", foreign_keys=[task_id])
    user = relationship("User")

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Temporarily commenting out enum imports as we use Any placeholders
# from src.models.task import TaskStatus, TaskPriority

# Using Any as placeholders for enums to allow the application to start
from typing import Any

TaskStatus = Any
TaskPriority = Any


# Base schema
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Project schemas
class ProjectBase(BaseModel):
    """Base schema for project information"""

    name: str
    description: Optional[str] = None
    owner_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "active"
    color: Optional[str] = None
    is_archived: bool = False


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating project information"""

    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    color: Optional[str] = None
    is_archived: Optional[bool] = None


class ProjectReadBasic(ProjectBase, BaseSchema):
    """Basic schema for reading project information"""

    owner: Dict[str, Any]  # Simplified owner info


class ProjectRead(ProjectReadBasic):
    """Full schema for reading project information"""

    task_count: int = 0
    completed_task_count: int = 0
    completion_percentage: float = 0.0


# Task schemas
class TaskCommentBase(BaseModel):
    """Base schema for task comment information"""

    task_id: int
    user_id: int
    content: str


class TaskCommentCreate(TaskCommentBase):
    """Schema for creating a new task comment"""

    pass


class TaskCommentUpdate(BaseModel):
    """Schema for updating task comment"""

    content: str


class TaskCommentRead(TaskCommentBase, BaseSchema):
    """Schema for reading task comment information"""

    user: Dict[str, Any]  # Simplified user info


class TaskBase(BaseModel):
    """Base schema for task information"""

    title: str
    description: Optional[str] = None
    status: TaskStatus = None
    priority: TaskPriority = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_percentage: int = 0
    creator_id: int
    project_id: Optional[int] = None
    parent_task_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating a new task"""

    assignee_ids: Optional[List[int]] = None  # IDs of users to assign


class TaskUpdate(BaseModel):
    """Schema for updating task information"""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_percentage: Optional[int] = None
    project_id: Optional[int] = None


class TaskAssigneeBase(BaseModel):
    """Base schema for task assignee information"""

    task_id: int
    user_id: int
    is_responsible: bool = False


class TaskAssigneeCreate(TaskAssigneeBase):
    """Schema for assigning a task to a user"""

    pass


class TaskAssigneeUpdate(BaseModel):
    """Schema for updating task assignee information"""

    is_responsible: bool = False


class TaskAssigneeRead(TaskAssigneeBase, BaseSchema):
    """Schema for reading task assignee information"""

    assigned_at: datetime
    user: Dict[str, Any]  # Simplified user info


class TaskReadBasic(TaskBase, BaseSchema):
    """Basic schema for reading task information"""

    completed_date: Optional[datetime] = None
    creator: Dict[str, Any]  # Simplified creator info
    assignees: List[TaskAssigneeRead] = []
    project: Optional[Dict[str, Any]] = None  # Simplified project info
    is_overdue: bool = False  # Calculated field


class TaskRead(TaskReadBasic):
    """Full schema for reading task information"""

    subtasks: List["TaskReadBasic"] = []
    comments: List[TaskCommentRead] = []
    parent_task: Optional[Dict[str, Any]] = None  # Simplified parent task info

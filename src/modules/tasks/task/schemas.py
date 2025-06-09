"""
Task schemas for request/response validation and serialization.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Base schemas
class TaskBase(BaseModel):
    """Base task schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(TaskStatus.TODO, description="Task status")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    estimated_hours: Optional[float] = Field(
        None, ge=0, description="Estimated hours to complete"
    )
    actual_hours: Optional[float] = Field(None, ge=0, description="Actual hours spent")
    start_date: Optional[datetime] = Field(None, description="Task start date")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    project_id: int = Field(..., description="Project ID this task belongs to")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    assignee_ids: Optional[List[int]] = Field(
        default_factory=list, description="List of user IDs to assign to this task"
    )
    dependency_ids: Optional[List[int]] = Field(
        default_factory=list, description="List of task IDs this task depends on"
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Task title"
    )
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    estimated_hours: Optional[float] = Field(
        None, ge=0, description="Estimated hours to complete"
    )
    actual_hours: Optional[float] = Field(None, ge=0, description="Actual hours spent")
    start_date: Optional[datetime] = Field(None, description="Task start date")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    project_id: Optional[int] = Field(
        None, description="Project ID this task belongs to"
    )
    assignee_ids: Optional[List[int]] = Field(
        None, description="List of user IDs to assign to this task"
    )
    dependency_ids: Optional[List[int]] = Field(
        None, description="List of task IDs this task depends on"
    )


# Response schemas
class UserResponse(BaseModel):
    """User response schema for task assignees."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    user_type: str


class ProjectResponse(BaseModel):
    """Project response schema for task project."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    status: str


class TaskDependencyResponse(BaseModel):
    """Task dependency response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority


class TaskResponse(BaseModel):
    """Task response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    project_id: int
    created_by_id: int

    # Related objects
    project: Optional[ProjectResponse] = None
    created_by: Optional[UserResponse] = None
    assignees: List[UserResponse] = Field(default_factory=list)
    dependencies: List[TaskDependencyResponse] = Field(default_factory=list)
    dependents: List[TaskDependencyResponse] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    """Task list response schema with pagination."""

    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Query parameters
class TaskQueryParams(BaseModel):
    """Query parameters for task filtering and pagination."""

    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    project_id: Optional[int] = Field(None, description="Filter by project ID")
    status: Optional[TaskStatus] = Field(None, description="Filter by task status")
    priority: Optional[TaskPriority] = Field(
        None, description="Filter by task priority"
    )
    assignee_id: Optional[int] = Field(None, description="Filter by assignee user ID")
    created_by_id: Optional[int] = Field(None, description="Filter by creator user ID")
    search: Optional[str] = Field(None, description="Search in title and description")
    tags: Optional[str] = Field(None, description="Filter by tags (comma-separated)")
    due_date_from: Optional[datetime] = Field(
        None, description="Filter tasks due after this date"
    )
    due_date_to: Optional[datetime] = Field(
        None, description="Filter tasks due before this date"
    )
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    )


class TaskStatsResponse(BaseModel):
    """Task statistics response schema."""

    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    under_review_tasks: int
    completed_tasks: int
    cancelled_tasks: int
    overdue_tasks: int
    tasks_by_priority: dict
    avg_completion_time: Optional[float] = None


# Error schemas
class TaskErrorResponse(BaseModel):
    """Task error response schema."""

    error: str
    detail: Optional[str] = None
    field_errors: Optional[dict] = None

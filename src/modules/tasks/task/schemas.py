from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# Task status
class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: Optional[int] = Field(None, ge=0)
    tags: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    project_id: int = Field(..., description="Project ID this task belongs to")
    assignee_ids: Optional[List[int]] = Field(default=[], description="List of user IDs to assign")
    dependency_ids: Optional[List[int]] = Field(default=[], description="List of task IDs this task depends on")

    @validator("due_date")
    def validate_due_date(cls, v, values):
        if v and "start_date" in values and values["start_date"]:
            if v <= values["start_date"]:
                raise ValueError("Due date must be after start date")
        return v

    @validator("estimated_hours")
    def validate_estimated_hours(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Estimated hours must be positive")
        return v


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    tags: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None

    @validator("actual_hours")
    def validate_actual_hours(cls, v):
        if v is not None and v < 0:
            raise ValueError("Actual hours cannot be negative")
        return v


class TaskAssignmentUpdate(BaseModel):
    assignee_ids: List[int] = Field(..., description="List of user IDs to assign to task")


class TaskDependencyUpdate(BaseModel):
    dependency_ids: List[int] = Field(..., description="List of task IDs this task depends on")


class UserSummary(BaseModel):
    id: int
    username: str
    email: str
    user_type: str

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    id: int
    name: str
    status: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    tags: Optional[str]
    start_date: Optional[date]
    due_date: Optional[date]
    completed_date: Optional[date]
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    # Related data
    project: Optional[ProjectSummary] = None
    assignees: List[UserSummary] = []
    dependencies: List[int] = []  # List of task IDs this task depends on
    dependent_tasks: List[int] = []  # List of task IDs that depend on this task

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    id: int
    name: str
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    project_id: int
    project_name: Optional[str] = None
    assignee_count: int = 0
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskStatsResponse(BaseModel):
    total_tasks: int
    not_started: int
    in_progress: int
    completed: int
    blocked: int
    cancelled: int
    overdue_tasks: int
    total_estimated_hours: Optional[int]
    total_actual_hours: Optional[int]

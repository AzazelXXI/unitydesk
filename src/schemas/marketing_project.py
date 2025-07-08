from pydantic import BaseModel, Field, EmailStr, validator, AnyHttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

# Temporarily commenting out enum imports as we use Any placeholders
# from src.models.project import (
#     ProjectStatus,
#     ProjectType,
#     WorkflowStage,
#     TaskPriority,
#     TaskStatus,
#     AssetType,
#     ReportType,
# )

# Using Any as placeholders for enums to allow the application to start
from typing import Any

ProjectStatus = Any
ProjectType = Any
WorkflowStage = Any
TaskPriority = Any
TaskStatus = Any
AssetType = Any
ReportType = Any


# Base Schemas with shared attributes
class BaseSchema(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Client Schemas
class ClientContactBase(BaseModel):
    name: str
    position: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ClientContactCreate(ClientContactBase):
    pass


class ClientContactUpdate(ClientContactBase):
    name: Optional[str] = None


class ClientContactRead(ClientContactBase, BaseSchema):
    pass


class ClientBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    website: Optional[AnyHttpUrl] = None
    logo_url: Optional[AnyHttpUrl] = None
    notes: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    company_name: Optional[str] = None


class ClientRead(ClientBase, BaseSchema):
    contacts: List[ClientContactRead] = []


# Project Team Member Schema
class ProjectTeamMember(BaseModel):
    user_id: int
    role: str
    joined_at: Optional[datetime] = None


# Marketing Project Schemas
class MarketingProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = None
    current_stage: WorkflowStage = None
    client_id: Optional[int] = None
    client_brief: Optional[str] = None
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    estimated_budget: Optional[float] = None
    actual_cost: Optional[float] = None
    owner_id: int


class MarketingProjectCreate(MarketingProjectBase):
    @validator("estimated_budget", pre=True)
    def parse_estimated_budget(cls, v):
        if v == "" or v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class MarketingProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    current_stage: Optional[WorkflowStage] = None
    client_id: Optional[int] = None
    client_brief: Optional[str] = None
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    estimated_budget: Optional[float] = None
    actual_cost: Optional[float] = None
    owner_id: Optional[int] = None


class MarketingProjectReadBasic(MarketingProjectBase, BaseSchema):
    pass


class MarketingProjectRead(MarketingProjectReadBasic):
    client: Optional[ClientRead] = None
    team_members: List[Dict[str, Any]] = []
    task_stats: Optional[Dict[str, int]] = None  # Summary of task status counts
    workflow_progress: Optional[float] = None  # Percentage of workflow completion


# Workflow Step Schemas
class WorkflowStepBase(BaseModel):
    project_id: int
    step_number: int
    name: str
    description: Optional[str] = None
    stage: WorkflowStage
    status: str = "pending"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None


class WorkflowStepCreate(WorkflowStepBase):
    pass


class WorkflowStepUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None


class WorkflowStepRead(WorkflowStepBase, BaseSchema):
    assigned_to: Optional[Dict[str, Any]] = None


# Marketing Task Schemas
class TaskCommentBase(BaseModel):
    task_id: int
    user_id: int
    content: str
    attachment_ids: Optional[List[int]] = None  # List of attachment IDs


class TaskCommentCreate(TaskCommentBase):
    pass


class TaskCommentUpdate(BaseModel):
    content: str


class TaskCommentRead(TaskCommentBase, BaseSchema):
    user: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None  # List of attachment metadata


class MarketingTaskBase(BaseModel):
    project_id: int
    workflow_step_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    status: TaskStatus = None
    priority: TaskPriority = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    creator_id: int
    assignee_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_percentage: int = 0


class MarketingTaskCreate(MarketingTaskBase):
    pass


class MarketingTaskUpdate(BaseModel):
    workflow_step_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_percentage: Optional[int] = None


class MarketingTaskReadBasic(MarketingTaskBase, BaseSchema):
    creator: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None


class MarketingTaskRead(MarketingTaskReadBasic):
    project: Optional[MarketingProjectReadBasic] = None
    workflow_step: Optional[WorkflowStepRead] = None
    subtasks: List["MarketingTaskReadBasic"] = []
    comments: List[TaskCommentRead] = []
    assets: List[Dict[str, Any]] = []


# Marketing Asset Schemas
class MarketingAssetBase(BaseModel):
    project_id: int
    related_task_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    asset_type: AssetType
    file_path: Optional[str] = None
    file_url: Optional[AnyHttpUrl] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    version: str = "1.0"
    is_final: bool = False
    creator_id: int
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    shared_with_client: bool = False
    client_feedback: Optional[str] = None


class MarketingAssetCreate(MarketingAssetBase):
    pass


class MarketingAssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[AnyHttpUrl] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    version: Optional[str] = None
    is_final: Optional[bool] = None
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    shared_with_client: Optional[bool] = None
    client_feedback: Optional[str] = None


class MarketingAssetRead(MarketingAssetBase, BaseSchema):
    creator: Optional[Dict[str, Any]] = None
    approved_by: Optional[Dict[str, Any]] = None
    project: Optional[MarketingProjectReadBasic] = None
    related_task: Optional[MarketingTaskReadBasic] = None


# Analytics Report Schemas
class AnalyticsReportBase(BaseModel):
    project_id: int
    report_type: ReportType
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    insights: Optional[str] = None
    recommendations: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_draft: bool = True
    creator_id: int
    approved_by_id: Optional[int] = None
    file_path: Optional[str] = None
    file_url: Optional[AnyHttpUrl] = None
    metrics: Optional[str] = None


class AnalyticsReportCreate(AnalyticsReportBase):
    pass


class AnalyticsReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    insights: Optional[str] = None
    recommendations: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_draft: Optional[bool] = None
    approved_by_id: Optional[int] = None
    file_path: Optional[str] = None
    file_url: Optional[AnyHttpUrl] = None
    metrics: Optional[str] = None


class AnalyticsReportRead(AnalyticsReportBase, BaseSchema):
    creator: Optional[Dict[str, Any]] = None
    approved_by: Optional[Dict[str, Any]] = None
    project: Optional[MarketingProjectReadBasic] = None

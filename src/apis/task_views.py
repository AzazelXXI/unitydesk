from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from src.database import get_db
from src.controllers.task_controller import TaskController

# Temporarily commenting out enum imports as we use Any placeholders
# from src.models.task import (
#     TaskStatus,
#     TaskPriority,
# )  # Changed from src.models_backup.marketing_project

# Using Any as placeholders for enums to allow the application to start
from typing import Any

TaskStatus = Any
TaskPriority = Any
from src.schemas.marketing_project import (
    WorkflowStepUpdate,
    WorkflowStepRead,
    MarketingTaskCreate,
    MarketingTaskUpdate,
    MarketingTaskRead,
    MarketingTaskReadBasic,
    TaskCommentCreate,
    TaskCommentRead,
)

# Configure logging
logger = logging.getLogger(__name__)

# Router for project-specific task endpoints
router = APIRouter(
    prefix="/api/projects",
    tags=["project tasks"],
    responses={404: {"description": "Not found"}},
)

# Router for general task endpoints
task_router = APIRouter(
    prefix="/api/tasks", tags=["tasks"], responses={404: {"description": "Not found"}}
)


# ==================== Workflow Step Endpoints ====================
@router.get("/{project_id}/workflow-steps", response_model=List[WorkflowStepRead])
async def get_workflow_steps(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all workflow steps for a project
    """
    return await TaskController.get_workflow_steps(project_id, db)


@router.get("/{project_id}/workflow-steps/{step_id}", response_model=WorkflowStepRead)
async def get_workflow_step(
    project_id: int, step_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Get a specific workflow step
    """
    return await TaskController.get_workflow_step(project_id, step_id, db)


@router.put("/{project_id}/workflow-steps/{step_id}", response_model=WorkflowStepRead)
async def update_workflow_step(
    project_id: int,
    step_id: int,
    step_data: WorkflowStepUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a workflow step
    """
    return await TaskController.update_workflow_step(project_id, step_id, step_data, db)


# ==================== Task Endpoints - Project Context ====================
@router.post(
    "/{project_id}/tasks",
    response_model=MarketingTaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int, task_data: MarketingTaskCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new task for a project
    """
    return await TaskController.create_task(project_id, task_data, db)


@router.get("/{project_id}/tasks", response_model=List[MarketingTaskReadBasic])
async def get_project_tasks(
    project_id: int,
    workflow_step_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[int] = None,
    parent_task_id: Optional[int] = None,
    search: Optional[str] = None,
    include_subtasks: bool = Query(
        False, description="Whether to include subtasks in the results"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tasks for a project with optional filtering
    """
    return await TaskController.get_project_tasks(
        project_id,
        workflow_step_id,
        status,
        priority,
        assignee_id,
        parent_task_id,
        search,
        include_subtasks,
        db,
    )


# ==================== Task Endpoints - Direct ====================
@task_router.get("/{task_id}", response_model=MarketingTaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific task by ID
    """
    return await TaskController.get_task(task_id, db)


@task_router.put("/{task_id}", response_model=MarketingTaskRead)
async def update_task(
    task_id: int, task_data: MarketingTaskUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update a task
    """
    return await TaskController.update_task(task_id, task_data, db)


@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a task
    """
    await TaskController.delete_task(task_id, db)


# ==================== Task Comment Endpoints ====================
@task_router.post("/{task_id}/comments", response_model=TaskCommentRead)
async def create_task_comment(
    task_id: int, comment_data: TaskCommentCreate, db: AsyncSession = Depends(get_db)
):
    """
    Add a comment to a task
    """
    return await TaskController.create_task_comment(task_id, comment_data, db)


@task_router.get("/{task_id}/comments", response_model=List[TaskCommentRead])
async def get_task_comments(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all comments for a task
    """
    return await TaskController.get_task_comments(task_id, db)


@task_router.put("/{task_id}/comments/{comment_id}", response_model=TaskCommentRead)
async def update_task_comment(
    task_id: int,
    comment_id: int,
    comment_data: TaskCommentCreate,  # Reusing TaskCommentCreate schema
    db: AsyncSession = Depends(get_db),
):
    """
    Update a task comment
    """
    return await TaskController.update_task_comment(
        task_id, comment_id, comment_data, db
    )


@task_router.delete(
    "/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_task_comment(
    task_id: int,
    comment_id: int,
    user_id: int = Query(..., description="ID of the user deleting the comment"),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a task comment
    """
    await TaskController.delete_task_comment(task_id, comment_id, user_id, db)

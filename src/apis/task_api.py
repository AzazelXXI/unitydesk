"""
Task API Routes - Real implementation with notifications
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import logging
from datetime import datetime

from src.database import get_db
from src.middleware.auth_middleware import get_current_user
from src.models.user import User
from src.models.task import Task, TaskStatusEnum, TaskPriorityEnum
from src.models.project import Project
from src.services.notification_service import NotificationService
from src.services.websocket_manager import websocket_manager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Router for task API endpoints
router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for API
class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    completed_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    project_id: int
    tags: Optional[str]

    class Config:
        from_attributes = True


class TaskCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: int
    status: Optional[TaskStatusEnum] = TaskStatusEnum.NOT_STARTED
    priority: Optional[TaskPriorityEnum] = TaskPriorityEnum.MEDIUM
    estimated_hours: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task"""
    try:
        # Create the task
        new_task = Task(
            name=task_data.name,
            description=task_data.description,
            project_id=task_data.project_id,
            status=task_data.status,
            priority=task_data.priority,
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        logger.info(f"Task {new_task.id} created by user {current_user.id}")
        return new_task

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a task with notifications to project members
    """
    try:
        # Get the current task
        task_query = select(Task).where(Task.id == task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        # Store old values for comparison
        old_status = task.status
        old_priority = task.priority

        # Update only provided fields
        update_data = task_data.model_dump(exclude_unset=True)

        # Handle status change logic
        if "status" in update_data:
            new_status = update_data["status"]

            # If changing to completed, set completed_date
            if (
                new_status == TaskStatusEnum.COMPLETED
                and old_status != TaskStatusEnum.COMPLETED
            ):
                update_data["completed_date"] = datetime.utcnow()

            # If changing from completed to something else, clear completed_date
            elif (
                old_status == TaskStatusEnum.COMPLETED
                and new_status != TaskStatusEnum.COMPLETED
            ):
                update_data["completed_date"] = None

        # Update the task
        if update_data:
            await db.execute(
                update(Task).where(Task.id == task_id).values(**update_data)
            )
            await db.commit()

            # Refresh the task object
            await db.refresh(task)
        # Send notifications for status changes
        if "status" in update_data and update_data["status"] != old_status:
            await NotificationService.notify_task_status_change(
                db=db,
                task_id=task_id,
                old_status=old_status.value,
                new_status=update_data["status"].value,
                updated_by_id=current_user.id,
            )

            # Send real-time WebSocket notification
            await websocket_manager.notify_task_status_change(
                db=db,
                task_id=task_id,
                old_status=old_status.value,
                new_status=update_data["status"].value,
                updated_by_user_id=current_user.id,
            )

        # Send notifications for priority changes
        if "priority" in update_data and update_data["priority"] != old_priority:
            # Get project details for notification
            project_query = select(Project).where(Project.id == task.project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()

            if project:
                await NotificationService.notify_project_update(
                    db=db,
                    project_id=project.id,
                    title=f"Task Priority Changed: {task.name}",
                    message=f"{current_user.name} changed task '{task.name}' priority from '{old_priority.value}' to '{update_data['priority'].value}' in project '{project.name}'",
                    updated_by_id=current_user.id,
                )

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific task
    """
    try:
        task_query = select(Task).where(Task.id == task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}",
        )


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[int] = None,
    status: Optional[TaskStatusEnum] = None,
    priority: Optional[TaskPriorityEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get tasks with optional filtering
    """
    try:
        query = select(Task)

        # Apply filters
        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)

        # Order by creation date (newest first)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        return tasks

    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}",
        )

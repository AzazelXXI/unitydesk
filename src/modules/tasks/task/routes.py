"""
Task API routes for CRUD operations and task management.
"""

import math
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from .schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskQueryParams,
    TaskStatsResponse,
    TaskErrorResponse,
)
from .service import TaskService
from .dependencies import (
    get_task_service,
    get_current_user,
    verify_task_access,
    verify_project_access,
    verify_task_edit_permission,
    verify_task_delete_permission,
    verify_task_assign_permission,
    validate_task_data,
    handle_service_error,
    TaskPermissions,
)
from src.models.user import User


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
    project=Depends(verify_project_access),
):
    """Create a new task."""
    try:
        # Validate permissions
        if not TaskPermissions.can_create_task(current_user, project):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create tasks in this project",
            )

        # Validate task data
        validate_task_data(task_data)

        # Create task
        task = await task_service.create_task(task_data, current_user.id)
        return task

    except ValueError as e:
        raise handle_service_error(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    project_id: int = Query(None, description="Filter by project ID"),
    status: str = Query(None, description="Filter by task status"),
    priority: str = Query(None, description="Filter by task priority"),
    assignee_id: int = Query(None, description="Filter by assignee user ID"),
    created_by_id: int = Query(None, description="Filter by creator user ID"),
    search: str = Query(None, description="Search in title and description"),
    tags: str = Query(None, description="Filter by tags (comma-separated)"),
    due_date_from: str = Query(
        None, description="Filter tasks due after this date (ISO format)"
    ),
    due_date_to: str = Query(
        None, description="Filter tasks due before this date (ISO format)"
    ),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """Get tasks with filtering, pagination, and sorting."""
    try:
        # Build query parameters
        params = TaskQueryParams(
            page=page,
            page_size=page_size,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            created_by_id=created_by_id,
            search=search,
            tags=tags,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        # Get tasks
        tasks, total = await task_service.get_tasks(params)

        # Calculate pagination info
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return TaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks",
        )


@router.get("/statistics", response_model=TaskStatsResponse)
async def get_task_statistics(
    project_id: int = Query(None, description="Filter by project ID"),
    user_id: int = Query(None, description="Filter by user ID"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """Get task statistics."""
    try:
        stats = await task_service.get_task_statistics(project_id, user_id)
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task statistics",
        )


@router.get("/my-tasks", response_model=TaskListResponse)
async def get_my_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    project_id: int = Query(None, description="Filter by project ID"),
    status: str = Query(None, description="Filter by task status"),
    priority: str = Query(None, description="Filter by task priority"),
    search: str = Query(None, description="Search in title and description"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """Get tasks assigned to the current user."""
    try:
        # Build query parameters
        params = TaskQueryParams(
            page=page,
            page_size=page_size,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=current_user.id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        # Get user tasks
        tasks, total = await task_service.get_user_tasks(current_user.id, params)

        # Calculate pagination info
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return TaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tasks",
        )


@router.get("/project/{project_id}", response_model=TaskListResponse)
async def get_project_tasks(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status: str = Query(None, description="Filter by task status"),
    priority: str = Query(None, description="Filter by task priority"),
    assignee_id: int = Query(None, description="Filter by assignee user ID"),
    search: str = Query(None, description="Search in title and description"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
    project=Depends(verify_project_access),
):
    """Get tasks for a specific project."""
    try:
        # Build query parameters
        params = TaskQueryParams(
            page=page,
            page_size=page_size,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        # Get project tasks
        tasks, total = await task_service.get_project_tasks(project_id, params)

        # Calculate pagination info
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return TaskListResponse(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project tasks",
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, task=Depends(verify_task_access)):
    """Get a specific task by ID."""
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
    task=Depends(verify_task_edit_permission),
):
    """Update an existing task."""
    try:
        # Validate task data
        validate_task_data(task_data)
        # Update task
        updated_task = await task_service.update_task(
            task_id, task_data, current_user.id
        )
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        return updated_task

    except ValueError as e:
        raise handle_service_error(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task",
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    task=Depends(verify_task_delete_permission),
):
    """Delete a task."""
    try:
        success = await task_service.delete_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        )


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    user_ids: List[int],
    task_service: TaskService = Depends(get_task_service),
    task=Depends(verify_task_assign_permission),
):
    """Assign users to a task."""
    try:
        updated_task = await task_service.assign_task(task_id, user_ids)
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        return updated_task

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign task",
        )


@router.post("/{task_id}/unassign", response_model=TaskResponse)
async def unassign_task(
    task_id: int,
    user_ids: List[int],
    task_service: TaskService = Depends(get_task_service),
    task=Depends(verify_task_assign_permission),
):
    """Unassign users from a task."""
    try:
        updated_task = await task_service.unassign_task(task_id, user_ids)
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        return updated_task

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unassign task",
        )


@router.post("/{task_id}/dependencies/{depends_on_id}")
async def add_task_dependency(
    task_id: int,
    depends_on_id: int,
    task_service: TaskService = Depends(get_task_service),
    task=Depends(verify_task_edit_permission),
):
    """Add a dependency between tasks."""
    try:
        success = await task_service.add_task_dependency(task_id, depends_on_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add dependency. Check if tasks exist and dependency is valid.",
            )

        return {"message": "Dependency added successfully"}

    except ValueError as e:
        raise handle_service_error(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add task dependency",
        )


@router.delete("/{task_id}/dependencies/{depends_on_id}")
async def remove_task_dependency(
    task_id: int,
    depends_on_id: int,
    task_service: TaskService = Depends(get_task_service),
    task=Depends(verify_task_edit_permission),
):
    """Remove a dependency between tasks."""
    try:
        success = await task_service.remove_task_dependency(task_id, depends_on_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found"
            )

        return {"message": "Dependency removed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove task dependency",
        )


# Note: Exception handlers are handled at the application level, not router level

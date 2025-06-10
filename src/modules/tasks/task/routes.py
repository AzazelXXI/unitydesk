from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from src.database import get_db
from .schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskAssignmentUpdate,
    TaskDependencyUpdate,
    TaskStatsResponse,
)
from .dependencies import (
    get_current_user,
    require_project_manager_or_team_leader,
    require_team_member,
    get_task_with_permission_check,
    get_project_with_permission_check,
)
from .service import TaskService

router = APIRouter(prefix="/api/v2/tasks", tags=["tasks-v2"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager_or_team_leader),
):
    """Create a new task - Only Project Managers and Team Leaders can create tasks"""
    return await TaskService.create_task(task_data, current_user.id, db)


@router.get("/", response_model=List[TaskListResponse])
async def get_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by task priority"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee user ID"),
    due_date_from: Optional[date] = Query(
        None, description="Filter tasks due from this date"
    ),
    due_date_to: Optional[date] = Query(
        None, description="Filter tasks due until this date"
    ),
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of tasks to return"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of tasks with optional filtering"""
    return await TaskService.get_tasks(
        user_id=current_user.id,
        project_id=project_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        skip=skip,
        limit=limit,
        db=db,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get task details by ID"""
    return await TaskService.get_task_by_id(task_id, current_user.id, db)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_team_member),
):
    """Update task - Team members can update tasks"""
    return await TaskService.update_task(task_id, task_data, current_user.id, db)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager_or_team_leader),
):
    """Delete task - Only Project Managers and Team Leaders can delete tasks"""
    await TaskService.delete_task(task_id, current_user.id, db)


@router.put("/{task_id}/assignments", response_model=TaskResponse)
async def update_task_assignments(
    task_id: int,
    assignment_data: TaskAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager_or_team_leader),
):
    """Update task assignments - Only Project Managers and Team Leaders can assign tasks"""
    return await TaskService.update_task_assignments(
        task_id, assignment_data, current_user.id, db
    )


@router.put("/{task_id}/dependencies", response_model=TaskResponse)
async def update_task_dependencies(
    task_id: int,
    dependency_data: TaskDependencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager_or_team_leader),
):
    """Update task dependencies - Only Project Managers and Team Leaders can manage dependencies"""
    return await TaskService.update_task_dependencies(
        task_id, dependency_data, current_user.id, db
    )


@router.get("/stats/summary", response_model=TaskStatsResponse)
async def get_task_statistics(
    project_id: Optional[int] = Query(
        None, description="Get stats for specific project"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get task statistics for projects user has access to"""
    return await TaskService.get_task_stats(current_user.id, project_id, db)


# Additional endpoints for workflow management


@router.put("/{task_id}/start")
async def start_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_team_member),
):
    """Start working on a task - updates status to IN_PROGRESS"""
    from .schemas import TaskUpdate, TaskStatus

    task_update = TaskUpdate(status=TaskStatus.IN_PROGRESS, start_date=date.today())

    return await TaskService.update_task(task_id, task_update, current_user.id, db)


@router.put("/{task_id}/complete")
async def complete_task(
    task_id: int,
    actual_hours: Optional[int] = Query(None, description="Actual hours spent on task"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_team_member),
):
    """Mark task as completed"""
    from .schemas import TaskUpdate, TaskStatus
    from datetime import datetime

    update_data = {"status": TaskStatus.COMPLETED, "completed_date": date.today()}

    if actual_hours is not None:
        update_data["actual_hours"] = actual_hours

    task_update = TaskUpdate(**update_data)

    return await TaskService.update_task(task_id, task_update, current_user.id, db)


@router.put("/{task_id}/block")
async def block_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_team_member),
):
    """Mark task as blocked"""
    from .schemas import TaskUpdate, TaskStatus

    task_update = TaskUpdate(status=TaskStatus.BLOCKED)

    return await TaskService.update_task(task_id, task_update, current_user.id, db)


@router.get("/my/assigned", response_model=List[TaskListResponse])
async def get_my_assigned_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by task priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get tasks assigned to the current user"""
    return await TaskService.get_tasks(
        user_id=current_user.id,
        assignee_id=current_user.id,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
        db=db,
    )


@router.get("/project/{project_id}", response_model=List[TaskListResponse])
async def get_project_tasks(
    project_id: int,
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by task priority"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    project=Depends(get_project_with_permission_check),
):
    """Get all tasks for a specific project"""
    return await TaskService.get_tasks(
        user_id=current_user.id,
        project_id=project_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        skip=skip,
        limit=limit,
        db=db,
    )

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.user import (
    User,
)
from src.models.task import Task
from src.models.project import Project
from src.models.association_tables import project_members, task_assignees
from src.middleware.auth_middleware import get_current_user as auth_get_current_user
from .exceptions import TaskNotFoundError, UnauthorizedTaskAccessError


async def get_current_user(current_user: User = Depends(auth_get_current_user)) -> User:
    """Get current authenticated user using the main auth system"""
    return current_user


async def require_project_manager_or_team_leader(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to have elevated permissions"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )
    return current_user


async def require_team_member(current_user: User = Depends(get_current_user)) -> User:
    """Require user to be a team member"""
    if not current_user.is_team_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team members can perform this action",
        )
    return current_user


async def get_task_with_permission_check(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    require_assignee: bool = False,
) -> Task:
    """Get task and check if user has permission to access it"""

    # Get task with project info
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise TaskNotFoundError(task_id)

    # Check if user has access to the project
    project_result = await db.execute(
        select(Project).where(Project.id == task.project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {task.project_id} not found",
        )

    # Check access permissions
    has_access = False

    # Project owner always has access
    if project.owner_id == current_user.id:
        has_access = True

    # Team members have access
    if not has_access:
        member_result = await db.execute(
            select(project_members)
            .where(project_members.c.project_id == task.project_id)
            .where(project_members.c.user_id == current_user.id)
        )
        has_access = member_result.first() is not None

    # If require_assignee is True, check if user is assigned to this task
    if require_assignee and has_access:
        assignee_result = await db.execute(
            select(task_assignees)
            .where(task_assignees.c.task_id == task_id)
            .where(task_assignees.c.user_id == current_user.id)
        )
        has_access = assignee_result.first() is not None

    if not has_access:
        raise UnauthorizedTaskAccessError(task_id)

    return task


async def get_project_with_permission_check(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Get project and check if user has permission to access it"""

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    # Check access permissions
    has_access = False

    # Project owner has access
    if project.owner_id == current_user.id:
        has_access = True

    # Team members have access
    if not has_access:
        member_result = await db.execute(
            select(project_members)
            .where(project_members.c.project_id == project_id)
            .where(project_members.c.user_id == current_user.id)
        )
        has_access = member_result.first() is not None

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to access project {project_id}",
        )

    return project

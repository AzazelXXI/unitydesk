"""
Task route dependencies and helper functions.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.user import User
from src.models.project import Project
from src.models.task import Task
from src.middleware.auth_middleware import get_current_user as get_authenticated_user
from .service import TaskService


def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    """Get task service instance."""
    return TaskService(db)


def get_current_user(current_user: User = Depends(get_authenticated_user)) -> User:
    """
    Get current authenticated user.
    This uses the existing authentication system.
    """
    return current_user


async def verify_task_access(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user)
) -> Task:
    """Verify user has access to a task."""
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # TODO: Implement proper access control based on project membership
    # For now, allow access to all tasks
    return task


async def verify_project_access(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Project:
    """Verify user has access to a project."""
    project_result = await db.execute(
        select(Project).filter(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # TODO: Implement proper access control based on project membership
    # For now, allow access to all projects
    return project


def verify_task_owner_or_admin(
    task: Task = Depends(verify_task_access),
    current_user: User = Depends(get_current_user)
) -> Task:
    """Verify user is task owner or admin."""
    if task.created_by_id != current_user.id and current_user.user_type not in ["system_admin", "project_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to modify this task"
        )
    return task


def verify_project_member_or_admin(
    project: Project = Depends(verify_project_access),
    current_user: User = Depends(get_current_user)
) -> Project:
    """Verify user is project member or admin."""
    # TODO: Implement proper project membership check
    # For now, allow access to all projects for admins and project managers
    if current_user.user_type not in ["system_admin", "project_manager"]:
        # Check if user is project member
        # This would require checking the project_members association table
        pass
    
    return project


class TaskPermissions:
    """Task permission helpers."""
    
    @staticmethod
    def can_create_task(user: User, project: Project) -> bool:
        """Check if user can create tasks in project."""
        # System admin and project managers can create tasks
        if user.user_type in ["system_admin", "project_manager"]:
            return True
        
        # Team leaders can create tasks in their projects
        if user.user_type == "team_leader":
            # TODO: Check if user is project member or team leader
            return True
        
        # Other users can create tasks if they are project members
        # TODO: Implement project membership check
        return True
    
    @staticmethod
    def can_edit_task(user: User, task: Task) -> bool:
        """Check if user can edit a task."""
        # System admin can edit any task
        if user.user_type == "system_admin":
            return True
        
        # Task creator can edit their task
        if task.created_by_id == user.id:
            return True
        
        # Project managers can edit tasks in their projects
        if user.user_type == "project_manager":
            # TODO: Check if user manages the project
            return True
        
        # Assignees can edit task status and time tracking
        # TODO: Check if user is assigned to the task
        return False
    
    @staticmethod
    def can_delete_task(user: User, task: Task) -> bool:
        """Check if user can delete a task."""
        # System admin can delete any task
        if user.user_type == "system_admin":
            return True
        
        # Task creator can delete their task
        if task.created_by_id == user.id:
            return True
        
        # Project managers can delete tasks in their projects
        if user.user_type == "project_manager":
            # TODO: Check if user manages the project
            return True
        
        return False
    
    @staticmethod
    def can_assign_task(user: User, task: Task) -> bool:
        """Check if user can assign/unassign tasks."""
        # System admin can assign any task
        if user.user_type == "system_admin":
            return True
        
        # Project managers and team leaders can assign tasks
        if user.user_type in ["project_manager", "team_leader"]:
            # TODO: Check project membership
            return True
        
        # Task creator can assign their task
        if task.created_by_id == user.id:
            return True
        
        return False


def check_task_permission(action: str):
    """
    Decorator factory for checking task permissions.
    
    Args:
        action: The action to check permissions for ('create', 'edit', 'delete', 'assign')
    """
    def dependency(
        task: Task = Depends(verify_task_access),
        current_user: User = Depends(get_current_user)
    ) -> Task:
        permissions = TaskPermissions()
        
        if action == "edit" and not permissions.can_edit_task(current_user, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to edit this task"
            )
        elif action == "delete" and not permissions.can_delete_task(current_user, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this task"
            )
        elif action == "assign" and not permissions.can_assign_task(current_user, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to assign this task"
            )
        
        return task
    
    return dependency


# Specific permission dependencies
verify_task_edit_permission = check_task_permission("edit")
verify_task_delete_permission = check_task_permission("delete")
verify_task_assign_permission = check_task_permission("assign")


# Helper functions
def validate_task_data(task_data) -> None:
    """Validate task data before processing."""
    if hasattr(task_data, 'due_date') and hasattr(task_data, 'start_date'):
        if task_data.due_date and task_data.start_date and task_data.due_date < task_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be earlier than start date"
            )


def handle_service_error(error: Exception) -> HTTPException:
    """Convert service errors to HTTP exceptions."""
    if isinstance(error, ValueError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    elif isinstance(error, PermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

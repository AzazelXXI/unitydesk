"""
Validation utilities for the tasks module.
"""
from datetime import datetime
from typing import List, Optional, Set
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.project import Project
from src.models.task import Task
from .exceptions import (
    TaskValidationError, InvalidDateRangeError, TaskDependencyError,
    CircularDependencyError, UserNotFoundError, ProjectNotFoundError
)


def validate_date_range(start_date: Optional[datetime], due_date: Optional[datetime]) -> None:
    """
    Validate that due date is not earlier than start date.
    
    Args:
        start_date: Task start date
        due_date: Task due date
        
    Raises:
        InvalidDateRangeError: If due date is before start date
    """
    if start_date and due_date and due_date < start_date:
        raise InvalidDateRangeError(
            start_date.isoformat(),
            due_date.isoformat()
        )


def validate_task_assignees(db: Session, assignee_ids: List[int], project_id: int) -> List[User]:
    """
    Validate that assignee users exist and can be assigned to tasks.
    
    Args:
        db: Database session
        assignee_ids: List of user IDs to assign
        project_id: Project ID for context
        
    Returns:
        List of valid User objects
        
    Raises:
        UserNotFoundError: If any user is not found
        TaskValidationError: If user cannot be assigned to tasks
    """
    if not assignee_ids:
        return []
    
    # Check if all users exist
    users = db.query(User).filter(User.id.in_(assignee_ids)).all()
    found_user_ids = {user.id for user in users}
    missing_user_ids = set(assignee_ids) - found_user_ids
    
    if missing_user_ids:
        raise UserNotFoundError(list(missing_user_ids)[0])
    
    # Validate that users can be assigned to tasks
    for user in users:
        if not _can_user_be_assigned_to_tasks(user):
            raise TaskValidationError(
                "assignee_ids",
                f"User {user.username} cannot be assigned to tasks",
                user.id
            )
    
    return users


def validate_task_dependencies(
    db: Session, 
    task_id: Optional[int], 
    dependency_ids: List[int], 
    project_id: int
) -> List[Task]:
    """
    Validate task dependencies.
    
    Args:
        db: Database session
        task_id: ID of the task being created/updated (None for new tasks)
        dependency_ids: List of task IDs this task depends on
        project_id: Project ID for context
        
    Returns:
        List of valid Task objects
        
    Raises:
        TaskValidationError: If dependencies are invalid
        CircularDependencyError: If dependencies would create a circular dependency
    """
    if not dependency_ids:
        return []
    
    # Check if all dependency tasks exist
    dependency_tasks = db.query(Task).filter(Task.id.in_(dependency_ids)).all()
    found_task_ids = {task.id for task in dependency_tasks}
    missing_task_ids = set(dependency_ids) - found_task_ids
    
    if missing_task_ids:
        raise TaskValidationError(
            "dependency_ids",
            f"Dependency tasks not found: {list(missing_task_ids)}",
            list(missing_task_ids)
        )
    
    # Validate that dependency tasks are in the same project
    for task in dependency_tasks:
        if task.project_id != project_id:
            raise TaskValidationError(
                "dependency_ids",
                f"Dependency task {task.id} is not in the same project",
                task.id
            )
    
    # Check for circular dependencies if task_id is provided (update scenario)
    if task_id:
        for dep_id in dependency_ids:
            if _would_create_circular_dependency(db, task_id, dep_id):
                raise CircularDependencyError(task_id, dep_id)
    
    # Check for self-dependency
    if task_id and task_id in dependency_ids:
        raise TaskValidationError(
            "dependency_ids",
            "Task cannot depend on itself",
            task_id
        )
    
    return dependency_tasks


def validate_project_exists(db: Session, project_id: int) -> Project:
    """
    Validate that a project exists.
    
    Args:
        db: Database session
        project_id: Project ID to validate
        
    Returns:
        Project object
        
    Raises:
        ProjectNotFoundError: If project is not found
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ProjectNotFoundError(project_id)
    
    return project


def validate_user_exists(db: Session, user_id: int) -> User:
    """
    Validate that a user exists.
    
    Args:
        db: Database session
        user_id: User ID to validate
        
    Returns:
        User object
        
    Raises:
        UserNotFoundError: If user is not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id)
    
    return user


def validate_task_title(title: str) -> None:
    """
    Validate task title.
    
    Args:
        title: Task title to validate
        
    Raises:
        TaskValidationError: If title is invalid
    """
    if not title or not title.strip():
        raise TaskValidationError("title", "Task title cannot be empty")
    
    if len(title) > 200:
        raise TaskValidationError("title", "Task title cannot exceed 200 characters")
    
    # Check for invalid characters (optional)
    invalid_chars = ['<', '>', '"', "'"]
    for char in invalid_chars:
        if char in title:
            raise TaskValidationError(
                "title", 
                f"Task title cannot contain '{char}' character"
            )


def validate_task_description(description: Optional[str]) -> None:
    """
    Validate task description.
    
    Args:
        description: Task description to validate
        
    Raises:
        TaskValidationError: If description is invalid
    """
    if description is not None and len(description) > 5000:
        raise TaskValidationError(
            "description", 
            "Task description cannot exceed 5000 characters"
        )


def validate_task_hours(estimated_hours: Optional[float], actual_hours: Optional[float]) -> None:
    """
    Validate task hour estimates.
    
    Args:
        estimated_hours: Estimated hours for the task
        actual_hours: Actual hours spent on the task
        
    Raises:
        TaskValidationError: If hours are invalid
    """
    if estimated_hours is not None:
        if estimated_hours < 0:
            raise TaskValidationError(
                "estimated_hours", 
                "Estimated hours cannot be negative"
            )
        if estimated_hours > 1000:  # Reasonable upper limit
            raise TaskValidationError(
                "estimated_hours", 
                "Estimated hours cannot exceed 1000"
            )
    
    if actual_hours is not None:
        if actual_hours < 0:
            raise TaskValidationError(
                "actual_hours", 
                "Actual hours cannot be negative"
            )
        if actual_hours > 1000:  # Reasonable upper limit
            raise TaskValidationError(
                "actual_hours", 
                "Actual hours cannot exceed 1000"
            )


def validate_task_tags(tags: Optional[str]) -> None:
    """
    Validate task tags.
    
    Args:
        tags: Comma-separated tags string
        
    Raises:
        TaskValidationError: If tags are invalid
    """
    if not tags:
        return
    
    if len(tags) > 500:
        raise TaskValidationError("tags", "Tags string cannot exceed 500 characters")
    
    # Parse and validate individual tags
    tag_list = [tag.strip() for tag in tags.split(',')]
    
    for tag in tag_list:
        if not tag:
            continue
        
        if len(tag) > 50:
            raise TaskValidationError("tags", f"Individual tag '{tag}' cannot exceed 50 characters")
        
        # Check for invalid characters in tags
        invalid_chars = ['<', '>', '"', "'", ';', '|']
        for char in invalid_chars:
            if char in tag:
                raise TaskValidationError(
                    "tags", 
                    f"Tag '{tag}' cannot contain '{char}' character"
                )


def validate_task_priority(priority: str) -> None:
    """
    Validate task priority.
    
    Args:
        priority: Task priority to validate
        
    Raises:
        TaskValidationError: If priority is invalid
    """
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if priority not in valid_priorities:
        raise TaskValidationError(
            "priority",
            f"Priority must be one of: {', '.join(valid_priorities)}",
            priority
        )


def validate_task_status(status: str) -> None:
    """
    Validate task status.
    
    Args:
        status: Task status to validate
        
    Raises:
        TaskValidationError: If status is invalid
    """
    valid_statuses = ['todo', 'in_progress', 'under_review', 'completed', 'cancelled']
    if status not in valid_statuses:
        raise TaskValidationError(
            "status",
            f"Status must be one of: {', '.join(valid_statuses)}",
            status
        )


def validate_task_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate task status transition.
    
    Args:
        current_status: Current task status
        new_status: New task status
        
    Raises:
        TaskValidationError: If transition is invalid
    """
    # Define valid status transitions
    valid_transitions = {
        'todo': ['in_progress', 'cancelled'],
        'in_progress': ['under_review', 'completed', 'cancelled', 'todo'],
        'under_review': ['completed', 'in_progress', 'cancelled'],
        'completed': ['in_progress'],  # Allow reopening completed tasks
        'cancelled': ['todo', 'in_progress']  # Allow reactivating cancelled tasks
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise TaskValidationError(
            "status",
            f"Invalid status transition from '{current_status}' to '{new_status}'"
        )


# Private helper functions
def _can_user_be_assigned_to_tasks(user: User) -> bool:
    """
    Check if a user can be assigned to tasks.
    
    Args:
        user: User to check
        
    Returns:
        bool: True if user can be assigned to tasks
    """
    # All user types can be assigned to tasks in this implementation
    # You might want to restrict certain user types based on business rules
    assignable_types = [
        'developer', 'tester', 'designer', 'team_leader', 
        'project_manager', 'system_admin'
    ]
    
    return user.user_type in assignable_types


def _would_create_circular_dependency(db: Session, task_id: int, depends_on_id: int) -> bool:
    """
    Check if adding a dependency would create a circular dependency.
    
    Args:
        db: Database session
        task_id: Task that would depend on depends_on_id
        depends_on_id: Task that task_id would depend on
        
    Returns:
        bool: True if it would create a circular dependency
    """
    if task_id == depends_on_id:
        return True
    
    # Use a set to track visited tasks to avoid infinite loops
    visited = set()
    stack = [depends_on_id]
    
    while stack:
        current_task_id = stack.pop()
        
        if current_task_id in visited:
            continue
        
        visited.add(current_task_id)
        
        # If we reach the original task, we have a circle
        if current_task_id == task_id:
            return True
        
        # Get tasks that the current task depends on
        from src.models.association_tables import task_dependencies
        dependencies = db.execute(
            task_dependencies.select().where(
                task_dependencies.c.task_id == current_task_id
            )
        ).fetchall()
        
        for dep in dependencies:
            if dep.depends_on_id not in visited:
                stack.append(dep.depends_on_id)
    
    return False


def validate_complete_task_data(
    db: Session,
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    status: str = "todo",
    estimated_hours: Optional[float] = None,
    actual_hours: Optional[float] = None,
    start_date: Optional[datetime] = None,
    due_date: Optional[datetime] = None,
    tags: Optional[str] = None,
    project_id: int = None,
    assignee_ids: Optional[List[int]] = None,
    dependency_ids: Optional[List[int]] = None,
    task_id: Optional[int] = None  # For updates
) -> dict:
    """
    Validate complete task data and return validated objects.
    
    Args:
        db: Database session
        title: Task title
        description: Task description
        priority: Task priority
        status: Task status
        estimated_hours: Estimated hours
        actual_hours: Actual hours
        start_date: Start date
        due_date: Due date
        tags: Tags string
        project_id: Project ID
        assignee_ids: List of assignee user IDs
        dependency_ids: List of dependency task IDs
        task_id: Task ID (for updates)
        
    Returns:
        dict: Dictionary with validated objects
        
    Raises:
        Various validation errors
    """
    # Validate basic fields
    validate_task_title(title)
    validate_task_description(description)
    validate_task_priority(priority)
    validate_task_status(status)
    validate_task_hours(estimated_hours, actual_hours)
    validate_date_range(start_date, due_date)
    validate_task_tags(tags)
    
    # Validate related objects
    project = validate_project_exists(db, project_id)
    assignees = validate_task_assignees(db, assignee_ids or [], project_id)
    dependencies = validate_task_dependencies(db, task_id, dependency_ids or [], project_id)
    
    return {
        'project': project,
        'assignees': assignees,
        'dependencies': dependencies
    }

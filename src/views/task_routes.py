"""
Task Web Router - Handles task web routes and Jinja template rendering

This module contains all task-related web routes for the CSA Platform, including:
- Task list views
- Task details
- Task creation and editing interfaces
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.modules.tasks.task.service import TaskService
from src.modules.tasks.project.service import ProjectService
from src.controllers.task_controller import TaskController
from src.controllers.project_controller import ProjectController

# Create router for task web routes
router = APIRouter(
    prefix="/tasks",
    tags=["web-tasks"],
    responses={404: {"description": "Page not found"}},
)

# Templates
templates = Jinja2Templates(directory="src/views")


@router.get("/")
async def tasks_home(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
    project_id: Optional[int] = None,
):
    """Tasks home page with real database data"""
    try:
        # Get tasks from database
        tasks_data = await TaskService.get_tasks(
            user_id=current_user.id, project_id=project_id, db=db
        )

        # Get projects and users for filters
        projects = await ProjectController.get_user_projects(current_user.id, db)
        users = await TaskController.get_users_for_assignment(db)

        # Get task statistics
        task_stats = await TaskService.get_task_stats(
            user_id=current_user.id, project_id=project_id, db=db
        )

        # Organize tasks by status for kanban board
        columns = {"todo": [], "in_progress": [], "review": [], "done": []}

        # Map database task statuses to board columns
        status_mapping = {
            "Not Started": "todo",
            "In Progress": "in_progress",
            "Completed": "done",
            "Blocked": "review",  # Blocked tasks go to review column
            "Cancelled": "done",  # Cancelled tasks go to done column
        }

        for task in tasks_data:
            # Get task status
            task_status = (
                task.status.value if hasattr(task.status, "value") else task.status
            )
            column = status_mapping.get(task_status, "todo")

            # Transform task for template compatibility
            task_item = {
                "id": task.id,
                "title": (
                    task.name
                    if task.name and task.name.strip()
                    else f"Untitled Task {task.id}"
                ),
                "description": task.description or "No description provided",
                "priority": (
                    task.priority.value.lower()
                    if hasattr(task.priority, "value")
                    else str(task.priority).lower()
                ),
                "due_date": (
                    task.due_date.strftime("%B %d, %Y")
                    if task.due_date
                    else "No due date"
                ),
                "is_overdue": False,  # Will calculate this properly
                "assignee": {
                    "name": (
                        f"User {task.assignee_count}"
                        if task.assignee_count > 0
                        else "Unassigned"
                    ),
                    "initials": "U",  # Will improve with real user data
                },
                "project_name": task.project_name or "Unknown Project",
            }

            # Check if task is overdue
            if task.due_date and task_status not in ["Completed", "Cancelled"]:
                from datetime import datetime

                task_item["is_overdue"] = task.due_date < datetime.now()

            columns[column].append(task_item)

        # Combine all tasks for list view
        all_tasks = []
        for status, tasks in columns.items():
            for task in tasks:
                task_copy = task.copy()
                task_copy["status"] = status
                all_tasks.append(task_copy)

        return templates.TemplateResponse(
            request=request,
            name="task/templates/modern_tasks.html",
            context={
                "request": request,
                "task_stats": task_stats,
                "projects": projects,
                "users": users,
                "columns": columns,
                "all_tasks": all_tasks,
                "current_user": current_user,
            },
        )

    except Exception as e:
        # Fallback to empty data if database query fails
        empty_columns = {"todo": [], "in_progress": [], "review": [], "done": []}
        return templates.TemplateResponse(
            request=request,
            name="task/templates/modern_tasks.html",
            context={
                "request": request,
                "task_stats": {
                    "total": 0,
                    "in_progress": 0,
                    "overdue": 0,
                    "completed": 0,
                },
                "projects": [],
                "users": [],
                "columns": empty_columns,
                "all_tasks": [],
                "current_user": current_user,
                "error": f"Failed to load tasks: {str(e)}",
            },
        )


@router.get("/{task_id}")
async def task_details(
    request: Request,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Task details page"""
    # In a real application, you would fetch the task from a database
    task = {
        "id": task_id,
        "title": "Example Task",
        "status": "In Progress",
        "due_date": "2025-04-30",
    }
    return templates.TemplateResponse(
        request=request,
        name="task/templates/task_details.html",
        context={
            "request": request,
            "title": "Task Details",
            "task": task,
            "current_user": current_user,
        },
    )


@router.get("/new")
async def new_task(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Create new task page"""
    try:
        projects = await ProjectController.get_user_projects(current_user.id, db)
        users = await TaskController.get_users_for_assignment(db)

        return templates.TemplateResponse(
            request=request,
            name="task/templates/new_task.html",
            context={
                "request": request,
                "title": "Create New Task",
                "projects": projects,
                "users": users,
                "current_user": current_user,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="task/templates/new_task.html",
            context={
                "request": request,
                "title": "Create New Task",
                "projects": [],
                "users": [],
                "current_user": current_user,
                "error": "Failed to load form data",
            },
        )


@router.get("/{task_id}/edit")
async def edit_task(
    request: Request,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Edit task page"""
    # In a real application, you would fetch the task from a database
    task = {
        "id": task_id,
        "title": "Example Task",
        "status": "In Progress",
        "due_date": "2025-04-30",
    }
    return templates.TemplateResponse(
        request=request,
        name="edit_task.html",
        context={
            "request": request,
            "title": "Edit Task",
            "task": task,
            "current_user": current_user,
        },
    )

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.modules.tasks.task.service import TaskService
from src.modules.tasks.project.service import ProjectService
from src.controllers.task_controller import TaskController
from src.controllers.project_controller import ProjectController

# --- Jinja2 Templates Configuration ---
# It's best practice to have a single, globally configured Jinja2Templates instance,
# often in your main.py or a central dependencies.py file.
# However, for this module to be self-contained or if a global instance isn't readily available,
# we initialize one here.
# The directory should be the root where Jinja2 looks for templates.
# Given that create_task.html extends "core/templates/base.html" and is located in "task/templates/",
# the common base directory for Jinja2 is 'src/views'.
TEMPLATES = Jinja2Templates(directory="src/views")


# --- Router Definition ---
task_web_router = APIRouter(
    prefix="/tasks",  # All routes in this router will start with /tasks
    tags=["Tasks Web Interface"],  # Tag for API docs, useful for separation
    include_in_schema=False,  # Typically, web-serving routes are not included in the OpenAPI schema
)


@task_web_router.get("/create", response_class=HTMLResponse)
async def get_create_task_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Serves the HTML page for creating a new task.
    The page is located at src/views/task/templates/create_task.html
    """
    # Get projects for dropdown
    try:
        projects = await ProjectController.get_user_projects(current_user.id, db)
        users = await TaskController.get_users_for_assignment(db)

        return TEMPLATES.TemplateResponse(
            "task/templates/create_task.html",
            {
                "request": request,
                "projects": projects,
                "users": users,
                "current_user": current_user,
            },
        )
    except Exception as e:
        return TEMPLATES.TemplateResponse(
            "task/templates/create_task.html",
            {
                "request": request,
                "projects": [],
                "users": [],
                "current_user": current_user,
                "error": "Failed to load project data",
            },
        )


# Add route for the task list page
@task_web_router.get("/", response_class=HTMLResponse)
async def get_task_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
):
    """
    Serves the HTML page for viewing all tasks.
    The page is located at src/views/task/templates/tasks.html
    """
    try:
        # Get tasks from database using TaskService
        tasks_data = await TaskService.get_tasks(
            user_id=current_user.id,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            db=db,
        )

        # Get task statistics
        task_stats = await TaskService.get_task_stats(
            user_id=current_user.id, project_id=project_id, db=db
        )

        # Get projects and users for filters
        projects = await ProjectController.get_user_projects(current_user.id, db)
        users = await TaskController.get_users_for_assignment(db)
        # Transform tasks for template compatibility
        tasks_for_template = []
        for task in tasks_data:
            tasks_for_template.append(
                {
                    "id": task.id,
                    "title": (
                        task.name
                        if task.name and task.name.strip()
                        else f"Untitled Task {task.id}"
                    ),
                    "status": (
                        task.status.value
                        if hasattr(task.status, "value")
                        else task.status
                    ),
                    "project": task.project_name or "Unknown Project",
                    "assignee": (
                        f"User {assignee_id}" if assignee_id else "Unassigned"
                    ),  # Will be improved with real user names
                    "due_date": (
                        task.due_date.strftime("%b %d, %Y")
                        if task.due_date
                        else "No due date"
                    ),
                    "priority": (
                        task.priority.value
                        if hasattr(task.priority, "value")
                        else task.priority
                    ),
                }
            )

        return TEMPLATES.TemplateResponse(
            "task/templates/tasks.html",
            {
                "request": request,
                "tasks": tasks_for_template,
                "task_stats": task_stats,
                "projects": projects,
                "users": users,
                "current_user": current_user,
            },
        )

    except Exception as e:
        # Fallback to empty data if database query fails
        return TEMPLATES.TemplateResponse(
            "task/templates/tasks.html",
            {
                "request": request,
                "tasks": [],
                "task_stats": {
                    "total_tasks": 0,
                    "in_progress": 0,
                    "overdue_tasks": 0,
                    "completed": 0,
                },
                "projects": [],
                "users": [],
                "current_user": current_user,
                "error": f"Failed to load tasks: {str(e)}",
            },
        )


@task_web_router.get("/board", response_class=HTMLResponse)
async def get_task_board_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
    project_id: Optional[int] = None,
):
    """
    Serves the HTML page for the task board (kanban) view.
    The page is located at src/views/task/templates/task_board.html
    """
    try:
        # Get tasks from database
        tasks_data = await TaskService.get_tasks(
            user_id=current_user.id, project_id=project_id, db=db
        )

        # Get projects for filters
        projects = await ProjectController.get_user_projects(current_user.id, db)
        users = await TaskController.get_users_for_assignment(db)

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

        return TEMPLATES.TemplateResponse(
            "task/templates/task_board.html",
            {
                "request": request,
                "columns": columns,
                "projects": projects,
                "users": users,
                "current_user": current_user,
            },
        )

    except Exception as e:
        # Fallback to empty columns if database query fails
        empty_columns = {"todo": [], "in_progress": [], "review": [], "done": []}
        return TEMPLATES.TemplateResponse(
            "task/templates/task_board.html",
            {
                "request": request,
                "columns": empty_columns,
                "projects": [],
                "users": [],
                "current_user": current_user,
                "error": f"Failed to load tasks: {str(e)}",
            },
        )

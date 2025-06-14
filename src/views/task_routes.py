"""
Task Web Router - Handles task web routes and Jinja template rendering

This module contains all task-related web routes for the CSA Platform, including:
- Task list views
- Task details
- Task creation and editing interfaces
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional
import os
import logging

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.controllers.task_controller import TaskController
from src.controllers.project_controller import ProjectController

# Configure logging
logger = logging.getLogger(__name__)

# Create router for task web routes
router = APIRouter(
    tags=["web-tasks"], responses={404: {"description": "Page not found"}}
)

# Templates - use absolute path to avoid issues
templates_path = "src/views"
templates = Jinja2Templates(directory=templates_path)


@router.get("/tasks/list", response_class=HTMLResponse)
async def task_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Display the task list view with all tasks in a table format
    """
    try:
        print(f"=== TASK LIST ACCESS ===")
        print(f"User: {current_user.name} (ID: {current_user.id})")
        print(f"User Type: {current_user.user_type}")

        # Query all tasks directly from database (managers can see all tasks)
        query = text(
            """
            SELECT 
                t.id,
                t.name as title,
                t.description,
                t.status,
                t.priority,
                t.estimated_hours,
                t.actual_hours,
                t.start_date,
                t.due_date,
                t.completed_date,
                t.created_at,
                t.updated_at,
                t.project_id,
                ta.user_id as assignee_id,
                u.name as assignee_name,
                p.name as project_name
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            LEFT JOIN projects p ON t.project_id = p.id
            ORDER BY t.created_at DESC
        """
        )

        result = await db.execute(query)
        task_rows = result.fetchall()

        print(f"Found {len(task_rows)} tasks in database")

        # Convert to task objects for list view
        tasks = []
        for row in task_rows:
            # Format due date
            due_date_formatted = "No due date"
            if row.due_date:
                due_date_formatted = row.due_date.strftime("%b %d, %Y")

            # Format status for display
            status = str(row.status).upper()
            status_display = status.replace("_", " ").title()

            # Format priority
            priority = str(row.priority).lower() if row.priority else "medium"

            task = {
                "id": row.id,
                "title": (
                    row.title
                    if row.title and row.title.strip()
                    else f"Untitled Task {row.id}"
                ),
                "project": row.project_name or "Unknown Project",
                "assignee": row.assignee_name or "Unassigned",
                "status": status_display,
                "due_date": due_date_formatted,
                "priority": priority.title(),
                "description": row.description or "No description provided",
                "estimated_hours": row.estimated_hours,
                "actual_hours": row.actual_hours,
            }
            tasks.append(task)

        # Create task stats for template
        task_stats = {
            "total_tasks": len(tasks),
            "in_progress": len([t for t in tasks if "Progress" in t["status"]]),
            "completed": len([t for t in tasks if "Completed" in t["status"]]),
            "overdue_tasks": 0,  # Can calculate this later if needed
        }

        # Get projects and users for filters
        try:
            projects = await ProjectController.get_user_projects(current_user.id, db)
            users = await TaskController.get_users_for_assignment(db)
        except Exception as e:
            print(f"Error loading filter data: {str(e)}")
            projects = []
            users = []

        return templates.TemplateResponse(
            "task/templates/tasks.html",
            {
                "request": request,
                "current_user": current_user,
                "tasks": tasks,
                "task_stats": task_stats,
                "projects": projects,
                "users": users,
                "title": "Task List",
            },
        )

    except Exception as e:
        print(f"ERROR in task list: {str(e)}")
        logger.error(f"Error loading task list: {str(e)}", exc_info=True)

        # Return error page with empty tasks
        return templates.TemplateResponse(
            "task/templates/tasks.html",
            {
                "request": request,
                "current_user": current_user,
                "tasks": [],
                "task_stats": {
                    "total_tasks": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "overdue_tasks": 0,
                },
                "projects": [],
                "users": [],
                "error": f"Could not load tasks: {str(e)}",
                "title": "Task List",
            },
        )


@router.get("/tasks", response_class=HTMLResponse)
async def task_board(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Display the task board with all tasks for managers
    """
    try:
        print(f"=== TASK BOARD ACCESS ===")
        print(f"User: {current_user.name} (ID: {current_user.id})")
        print(f"User Type: {current_user.user_type}")
        print(f"🔍 DEBUG: Starting database query...")

        # Query all tasks directly from database (managers can see all tasks)
        query = text(
            """
            SELECT 
                t.id,
                t.name as title,
                t.description,
                t.status,
                t.priority,
                t.estimated_hours,
                t.actual_hours,
                t.start_date,
                t.due_date,
                t.completed_date,
                t.created_at,
                t.updated_at,
                t.project_id,
                ta.user_id as assignee_id,
                u.name as assignee_name
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            ORDER BY t.created_at DESC
        """
        )

        print(f"🔍 DEBUG: Executing database query...")
        result = await db.execute(query)
        print(f"🔍 DEBUG: Query executed, fetching results...")
        task_rows = result.fetchall()

        print(f"Found {len(task_rows)} tasks in database")
        print(f"🔍 DEBUG: Processing task data...")

        # Convert to task objects
        tasks = []
        for i, row in enumerate(task_rows):
            print(f"🔍 DEBUG: Processing task {i+1}/{len(task_rows)}")
            task = {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "status": row.status,
                "priority": row.priority,
                "estimated_hours": row.estimated_hours,
                "actual_hours": row.actual_hours,
                "start_date": row.start_date,
                "due_date": row.due_date,
                "completed_date": row.completed_date,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "project_id": row.project_id,
                "assignee": (
                    {
                        "id": row.assignee_id,
                        "name": row.assignee_name,
                    }
                    if row.assignee_id
                    else None
                ),
            }
            tasks.append(task)

        print(f"🔍 DEBUG: Organizing tasks by status...")
        # Organize tasks by status - use 'columns' to match template expectations
        columns = {"todo": [], "in_progress": [], "done": []}

        for task in tasks:
            status = str(task["status"]).upper()
            print(f"Task: {task['title']} - Status: {status}")

            if status in ["NOT_STARTED", "PENDING", "TODO"]:
                columns["todo"].append(task)
            elif status in ["IN_PROGRESS", "ACTIVE", "WORKING"]:
                columns["in_progress"].append(task)
            elif status in ["COMPLETED", "DONE", "FINISHED"]:
                columns["done"].append(task)
            else:  # Default unknown statuses to todo
                columns["todo"].append(task)

        print(
            f"Task distribution: TODO={len(columns['todo'])}, IN_PROGRESS={len(columns['in_progress'])}, DONE={len(columns['done'])}"
        )

        print(f"🔍 DEBUG: Creating task stats...")
        # Create task stats for template
        task_stats = {
            "total": len(tasks),
            "in_progress": len(columns["in_progress"]),
            "completed": len(columns["done"]),
            "overdue": 0,  # Can calculate this later if needed
        }

        print(f"🔍 DEBUG: Combining tasks for list view...")
        # Combine all tasks for list view
        all_tasks = []
        for status, task_list in columns.items():
            for task in task_list:
                task_copy = task.copy()
                task_copy["status"] = status
                all_tasks.append(task_copy)

        print(f"🔍 DEBUG: Rendering template...")
        template_context = {
            "request": request,
            "current_user": current_user,
            "columns": columns,  # Template expects 'columns'
            "task_stats": task_stats,
            "all_tasks": all_tasks,
            "total_tasks": len(tasks),
            "projects": [],  # Empty for now
            "users": [],  # Empty for now
        }

        print(f"🔍 DEBUG: Template context prepared, calling TemplateResponse...")
        response = templates.TemplateResponse(
            "task/templates/task_board.html", template_context
        )
        print(f"🔍 DEBUG: Template rendered successfully!")
        return response

    except Exception as e:
        print(f"ERROR in task board: {str(e)}")
        logger.error(f"Error loading task board: {str(e)}", exc_info=True)

        # Return error page with empty tasks
        empty_columns = {"todo": [], "in_progress": [], "done": []}
        return templates.TemplateResponse(
            "task/templates/task_board.html",
            {
                "request": request,
                "current_user": current_user,
                "columns": empty_columns,
                "task_stats": {
                    "total": 0,
                    "in_progress": 0,
                    "overdue": 0,
                    "completed": 0,
                },
                "all_tasks": [],
                "total_tasks": 0,
                "projects": [],
                "users": [],
                "error": f"Could not load tasks: {str(e)}",
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

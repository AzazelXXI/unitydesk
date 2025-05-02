"""
Task Web Router - Handles task web routes and Jinja template rendering

This module contains all task-related web routes for the CSA Platform, including:
- Task list views
- Task details
- Task creation and editing interfaces
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Create router for task web routes
router = APIRouter(
    prefix="/tasks",
    tags=["web-tasks"],
    responses={404: {"description": "Page not found"}},
)

# Templates
templates = Jinja2Templates(directory="src/web/task/templates")

@router.get("/")
async def tasks_home(request: Request):
    """Tasks home page"""
    return templates.TemplateResponse(
        request=request, 
        name="tasks.html", 
        context={"request": request, "title": "Tasks"}
    )

@router.get("/{task_id}")
async def task_details(request: Request, task_id: int):
    """Task details page"""
    # In a real application, you would fetch the task from a database
    task = {"id": task_id, "title": "Example Task", "status": "In Progress", "due_date": "2025-04-30"}
    return templates.TemplateResponse(
        request=request, 
        name="task_details.html", 
        context={"request": request, "title": "Task Details", "task": task}
    )

@router.get("/new")
async def new_task(request: Request):
    """Create new task page"""
    return templates.TemplateResponse(
        request=request, 
        name="new_task.html", 
        context={"request": request, "title": "Create New Task"}
    )

@router.get("/{task_id}/edit")
async def edit_task(request: Request, task_id: int):
    """Edit task page"""
    # In a real application, you would fetch the task from a database
    task = {"id": task_id, "title": "Example Task", "status": "In Progress", "due_date": "2025-04-30"}
    return templates.TemplateResponse(
        request=request, 
        name="edit_task.html", 
        context={"request": request, "title": "Edit Task", "task": task}
    )

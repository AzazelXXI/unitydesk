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
    # Sample data for task board view
    task_stats = {
        "total": 48,
        "in_progress": 12,
        "overdue": 5,
        "completed": 23
    }
    
    # Sample projects for filters
    projects = [
        {"id": 1, "name": "Website Redesign"},
        {"id": 2, "name": "Mobile App Development"},
        {"id": 3, "name": "Marketing Campaign"}
    ]
    
    # Sample users for filters and assignments
    users = [
        {"id": 1, "name": "John Smith"},
        {"id": 2, "name": "Jane Doe"},
        {"id": 3, "name": "Bob Johnson"}
    ]
    
    # Sample tasks organized by status columns
    columns = {
        "todo": [
            {
                "id": 1,
                "title": "Design homepage mockup",
                "description": "Create wireframes for the new homepage",
                "priority": "high",
                "due_date": "May 5, 2025",
                "is_overdue": False,
                "assignee": {"name": "Jane Doe", "initials": "JD"}
            },
            {
                "id": 2,
                "title": "Research competitors",
                "description": "Analyze top 5 competitor websites",
                "priority": "medium",
                "due_date": "May 8, 2025",
                "is_overdue": False,
                "assignee": {"name": "John Smith", "initials": "JS"}
            }
        ],
        "in_progress": [
            {
                "id": 3,
                "title": "Develop API endpoints",
                "description": "Implement REST API for user authentication",
                "priority": "high",
                "due_date": "April 30, 2025",
                "is_overdue": True,
                "assignee": {"name": "Bob Johnson", "initials": "BJ"}
            },
            {
                "id": 4,
                "title": "Create dashboard layout",
                "description": "Implement responsive dashboard layout",
                "priority": "medium",
                "due_date": "May 3, 2025",
                "is_overdue": False,
                "assignee": {"name": "Jane Doe", "initials": "JD"}
            }
        ],
        "review": [
            {
                "id": 5,
                "title": "User feedback integration",
                "description": "Implement changes based on user testing",
                "priority": "medium",
                "due_date": "May 2, 2025",
                "is_overdue": False,
                "assignee": {"name": "John Smith", "initials": "JS"}
            }
        ],
        "done": [
            {
                "id": 6,
                "title": "Project kickoff meeting",
                "description": "Initial meeting with stakeholders",
                "priority": "low",
                "due_date": "April 25, 2025",
                "is_overdue": False,
                "assignee": {"name": "Jane Doe", "initials": "JD"}
            },
            {
                "id": 7,
                "title": "Requirements gathering",
                "description": "Document project requirements",
                "priority": "medium",
                "due_date": "April 27, 2025",
                "is_overdue": False,
                "assignee": {"name": "Bob Johnson", "initials": "BJ"}
            }
        ]
    }
    
    # Combine all tasks for list view
    all_tasks = []
    for status, tasks in columns.items():
        for task in tasks:
            task_copy = task.copy()
            task_copy["status"] = status
            task_copy["project"] = {"name": "Website Redesign"}  # Sample project name
            all_tasks.append(task_copy)
    
    return templates.TemplateResponse(
        request=request, 
        name="modern_tasks.html", 
        context={
            "request": request,
            "task_stats": task_stats,
            "projects": projects,
            "users": users,
            "columns": columns,
            "all_tasks": all_tasks
        }
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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

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
async def get_create_task_page(request: Request):
    """
    Serves the HTML page for creating a new task.
    The page is located at src/views/task/templates/create_task.html
    """
    return TEMPLATES.TemplateResponse(
        "task/templates/create_task.html", {"request": request}
    )


# Add route for the task list page
@task_web_router.get("/", response_class=HTMLResponse)
async def get_task_list_page(request: Request):
    """
    Serves the HTML page for viewing all tasks.
    The page is located at src/views/task/templates/tasks.html
    """
    # Sample data - in a real application, this would come from a database
    tasks_data = [
        {
            "id": 1,
            "title": "Complete project proposal",
            "status": "In Progress",
            "project": "Website Redesign",
            "assignee": "Jane Doe",
            "due_date": "Apr 26, 2025",
            "priority": "High",
        },
        {
            "id": 2,
            "title": "Meet with client",
            "status": "Scheduled",
            "project": "Mobile App Development",
            "assignee": "John Smith",
            "due_date": "Apr 25, 2025",
            "priority": "Medium",
        },
        {
            "id": 3,
            "title": "Review requirements",
            "status": "Completed",
            "project": "Website Redesign",
            "assignee": "Bob Johnson",
            "due_date": "Apr 23, 2025",
            "priority": "Low",
        },
    ]
    return TEMPLATES.TemplateResponse(
        "task/templates/tasks.html", {"request": request, "tasks": tasks_data}
    )


@task_web_router.get("/board", response_class=HTMLResponse)
async def get_task_board_page(request: Request):
    """
    Serves the HTML page for the task board (kanban) view.
    The page is located at src/views/task/templates/task_board.html
    """
    # Sample data with columns for kanban board
    columns = {
        "todo": [
            {
                "id": 1,
                "title": "Design homepage mockup",
                "description": "Create wireframes for the new homepage",
                "priority": "high",
                "due_date": "May 5, 2025",
                "is_overdue": False,
                "assignee": {"name": "Jane Doe", "initials": "JD"},
            },
            {
                "id": 2,
                "title": "Research competitors",
                "description": "Analyze top 5 competitor websites",
                "priority": "medium",
                "due_date": "May 8, 2025",
                "is_overdue": False,
                "assignee": {"name": "John Smith", "initials": "JS"},
            },
        ],
        "in_progress": [
            {
                "id": 3,
                "title": "Develop API endpoints",
                "description": "Implement REST API for user authentication",
                "priority": "high",
                "due_date": "April 30, 2025",
                "is_overdue": True,
                "assignee": {"name": "Bob Johnson", "initials": "BJ"},
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
                "assignee": {"name": "John Smith", "initials": "JS"},
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
                "assignee": {"name": "Jane Doe", "initials": "JD"},
            }
        ],
    }
    return TEMPLATES.TemplateResponse(
        "task/templates/task_board.html", {"request": request, "columns": columns}
    )

# filepath: d:\projects\CSA\csa-hello\src\web\__init__.py
"""
Web Routes Package

This package contains all web routes for the CSA Platform that render HTML templates.
The routes are organized by module, with each module having its own router file.
"""

# Import all routers for easy access
from src.views.core_routes import router as core_router
from src.views.dashboard_routes import router as dashboard_router

# Meeting module will be developed later
# from src.views.meeting_routes import router as meeting_router
from src.views.calendar_routes import router as calendar_router
from src.views.projects_routes import router as projects_router
from src.views.task.web_routes import task_web_router  # Specific routes first
from src.views.task_routes import router as task_router  # Dynamic routes second
from src.views.user_routes import router as user_router
from src.views.public_user_routes import public_user_router
from src.controllers.project_controller import router as project_controller_router

# Define the list of all web routers for easy inclusion in the main application
web_routers = [
    core_router,
    dashboard_router,
    # meeting_router,  # Hidden for now, will be developed later
    calendar_router,
    projects_router,
    task_web_router,  # Specific routes like /tasks/create (FIRST)
    task_router,      # Dynamic routes like /tasks/{task_id} (SECOND)
    user_router,
    public_user_router,  # /public-user prefix
    project_controller_router,  # Modern project templates
]

__all__ = [
    "web_routers",
    "core_router",
    "dashboard_router",
    "meeting_router",
    "calendar_router",
    "projects_router",
    "task_router",
    "user_router",
]

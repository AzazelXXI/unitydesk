# filepath: d:\projects\CSA\csa-hello\src\web\__init__.py
"""
Web Routes Package

This package contains all web routes for the CSA Platform that render HTML templates.
The routes are organized by module, with each module having its own router file.
"""

# Import all routers for easy access
from src.web.core_routes import router as core_router
from src.web.dashboard_routes import router as dashboard_router
from src.web.meeting_routes import router as meeting_router
from src.web.calendar_routes import router as calendar_router
from src.web.projects_routes import router as projects_router
from src.web.task_routes import router as task_router
from src.web.user_routes import router as user_router

# Define the list of all web routers for easy inclusion in the main application
web_routers = [
    core_router,
    dashboard_router,
    meeting_router,
    calendar_router,
    projects_router,
    task_router,
    user_router,
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

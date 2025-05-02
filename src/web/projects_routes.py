"""
Projects Web Router - Handles project web routes and Jinja template rendering

This module contains all project-related web routes for the CSA Platform, including:
- Projects dashboard
- Project details
- Project creation and editing interfaces
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Create router for projects web routes
router = APIRouter(
    prefix="/projects",
    tags=["web-projects"],
    responses={404: {"description": "Page not found"}},
)

# Templates
templates = Jinja2Templates(directory="src/web/projects/templates")

@router.get("/")
async def projects_home(request: Request):
    """Projects home page"""
    return templates.TemplateResponse(
        request=request, 
        name="projects.html", 
        context={"request": request, "title": "Projects"}
    )

@router.get("/{project_id}")
async def project_details(request: Request, project_id: int):
    """Project details page"""
    # In a real application, you would fetch the project from a database
    project = {"id": project_id, "name": "Example Project", "status": "In Progress"}
    return templates.TemplateResponse(
        request=request, 
        name="project_details.html", 
        context={"request": request, "title": "Project Details", "project": project}
    )

@router.get("/new")
async def new_project(request: Request):
    """Create new project page"""
    return templates.TemplateResponse(
        request=request, 
        name="new_project.html", 
        context={"request": request, "title": "Create New Project"}
    )

@router.get("/{project_id}/edit")
async def edit_project(request: Request, project_id: int):
    """Edit project page"""
    # In a real application, you would fetch the project from a database
    project = {"id": project_id, "name": "Example Project", "status": "In Progress"}
    return templates.TemplateResponse(
        request=request, 
        name="edit_project.html", 
        context={"request": request, "title": "Edit Project", "project": project}
    )

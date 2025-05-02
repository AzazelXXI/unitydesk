"""
Dashboard Web Router - Handles dashboard web routes and Jinja template rendering

This module contains all dashboard-related web routes for the CSA Platform, including:
- Dashboard home page
- Analytics dashboard
- Projects dashboard
- Tasks dashboard
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Create router for dashboard web routes
router = APIRouter(
    prefix="/dashboard",
    tags=["web-dashboard"],
    responses={404: {"description": "Page not found"}},
)

# Templates - Use dashboard-specific templates
templates = Jinja2Templates(directory="src/web/dashboard/templates")

@router.get("/")
async def dashboard_home(request: Request):
    """Dashboard home page"""
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"request": request})

@router.get("/analytics")
async def dashboard_analytics(request: Request):
    """Analytics dashboard page"""
    return templates.TemplateResponse(request=request, name="analytics.html", context={"request": request})

@router.get("/projects")
async def dashboard_projects(request: Request):
    """Projects dashboard page"""
    return templates.TemplateResponse(request=request, name="projects.html", context={"request": request})

@router.get("/tasks")
async def dashboard_tasks(request: Request):
    """Tasks dashboard page"""
    return templates.TemplateResponse(request=request, name="tasks.html", context={"request": request})

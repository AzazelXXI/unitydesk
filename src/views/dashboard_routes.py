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
    # Sample data for dashboard
    dashboard = {
        "total_tasks": 48,
        "pending_tasks": 25,
        "completed_tasks": 23,
        "overdue_tasks": 5,
        "active_projects": 12,
        
        # Sample recent tasks
        "recent_tasks": [
            {
                "title": "Complete API Documentation",
                "status": "in_progress",
                "project_name": "Website Redesign",
                "due_date": "May 3, 2025",
                "is_overdue": False,
                "is_due_soon": True,
                "assignee": "Jane Doe"
            },
            {
                "title": "Fix Authentication Bug",
                "status": "todo",
                "project_name": "Mobile App Development",
                "due_date": "April 29, 2025",
                "is_overdue": True,
                "is_due_soon": False,
                "assignee": "Bob Johnson"
            },
            {
                "title": "Design User Profile Page",
                "status": "review",
                "project_name": "Website Redesign",
                "due_date": "May 5, 2025",
                "is_overdue": False,
                "is_due_soon": False,
                "assignee": "Alice Brown"
            },
            {
                "title": "Implement Analytics Dashboard",
                "status": "in_progress",
                "project_name": "Mobile App Development",
                "due_date": "May 8, 2025",
                "is_overdue": False,
                "is_due_soon": False,
                "assignee": "John Smith"
            }
        ],
        
        # Sample active projects
        "active_project_data": [
            {
                "name": "Website Redesign",
                "progress": 65,
                "client_name": "Acme Corporation",
                "end_date": "May 15, 2025",
                "days_remaining": 14,
                "team": [
                    {"name": "John Smith", "initials": "JS"},
                    {"name": "Jane Doe", "initials": "JD"},
                    {"name": "Bob Johnson", "initials": "BJ"}
                ]
            },
            {
                "name": "Mobile App Development",
                "progress": 35,
                "client_name": "Globex Industries",
                "end_date": "June 30, 2025",
                "days_remaining": 60,
                "team": [
                    {"name": "Bob Johnson", "initials": "BJ"},
                    {"name": "Alice Brown", "initials": "AB"},
                    {"name": "Jane Doe", "initials": "JD"},
                    {"name": "John Smith", "initials": "JS"}
                ]
            },
            {
                "name": "CRM Integration",
                "progress": 20,
                "client_name": "Initech",
                "end_date": "May 30, 2025",
                "days_remaining": 29,
                "team": [
                    {"name": "Bob Johnson", "initials": "BJ"},
                    {"name": "Jane Doe", "initials": "JD"}
                ]
            }
        ],
        
        # Sample recent activities
        "recent_activities": [
            {
                "user": "Jane Doe",
                "description": "Completed task <strong>Update Navigation Menu</strong>",
                "time_ago": "10 minutes ago"
            },
            {
                "user": "Bob Johnson",
                "description": "Added comment on <strong>API Integration Issue</strong>",
                "time_ago": "1 hour ago"
            },
            {
                "user": "John Smith",
                "description": "Created project <strong>Client Portal Redesign</strong>",
                "time_ago": "3 hours ago"
            },
            {
                "user": "Alice Brown",
                "description": "Uploaded 5 new design files to <strong>Mobile App Development</strong>",
                "time_ago": "Yesterday at 4:30 PM"
            },
            {
                "user": "System",
                "description": "Scheduled server maintenance for <strong>May 5, 2025</strong>",
                "time_ago": "Yesterday at 2:15 PM"
            }
        ]
    }
    
    return templates.TemplateResponse(
        request=request, 
        name="modern_dashboard.html", 
        context={
            "request": request,
            "dashboard": dashboard
        }
    )

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

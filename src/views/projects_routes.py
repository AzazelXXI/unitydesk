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
    # Sample project statistics
    stats = {
        "total_projects": 24,
        "active_projects": 12,
        "completed_projects": 8,
        "on_hold_projects": 3,
        "avg_completion": 68
    }
    
    # Sample clients for filters
    clients = [
        {"id": 1, "name": "Acme Corporation"},
        {"id": 2, "name": "Globex Industries"},
        {"id": 3, "name": "Initech"}
    ]
    
    # Sample departments for filters
    departments = [
        {"id": 1, "name": "Marketing"},
        {"id": 2, "name": "Engineering"},
        {"id": 3, "name": "Design"}
    ]
    
    # Sample users for team members
    users = [
        {"id": 1, "name": "John Smith"},
        {"id": 2, "name": "Jane Doe"},
        {"id": 3, "name": "Bob Johnson"},
        {"id": 4, "name": "Alice Brown"}
    ]
    
    # Sample projects
    projects = [
        {
            "id": 1,
            "name": "Website Redesign",
            "description": "Completely revamp the company website with modern design and improved UX",
            "status": "active",
            "progress": 65,
            "client": {"id": 1, "name": "Acme Corporation"},
            "department": {"id": 3, "name": "Design"},
            "start_date": "2025-04-01",
            "end_date": "May 15, 2025",
            "tasks_count": 24,
            "team": [
                {"id": 1, "name": "John Smith", "initials": "JS"},
                {"id": 2, "name": "Jane Doe", "initials": "JD"},
                {"id": 3, "name": "Bob Johnson", "initials": "BJ"}
            ],
            "image_url": "/static/images/project1.jpg"
        },
        {
            "id": 2,
            "name": "Mobile App Development",
            "description": "Build a cross-platform mobile application for customer engagement",
            "status": "active",
            "progress": 35,
            "client": {"id": 2, "name": "Globex Industries"},
            "department": {"id": 2, "name": "Engineering"},
            "start_date": "2025-03-15",
            "end_date": "June 30, 2025",
            "tasks_count": 36,
            "team": [
                {"id": 3, "name": "Bob Johnson", "initials": "BJ"},
                {"id": 4, "name": "Alice Brown", "initials": "AB"},
                {"id": 2, "name": "Jane Doe", "initials": "JD"},
                {"id": 1, "name": "John Smith", "initials": "JS"}
            ],
            "image_url": "/static/images/project2.jpg"
        },
        {
            "id": 3,
            "name": "Marketing Campaign",
            "description": "Q2 digital marketing campaign for product launch",
            "status": "completed",
            "progress": 100,
            "client": {"id": 1, "name": "Acme Corporation"},
            "department": {"id": 1, "name": "Marketing"},
            "start_date": "2025-01-15",
            "end_date": "April 15, 2025",
            "tasks_count": 18,
            "team": [
                {"id": 1, "name": "John Smith", "initials": "JS"},
                {"id": 4, "name": "Alice Brown", "initials": "AB"}
            ],
            "image_url": "/static/images/project3.jpg"
        },
        {
            "id": 4,
            "name": "CRM Integration",
            "description": "Integrate new CRM system with existing tools",
            "status": "on_hold",
            "progress": 20,
            "client": {"id": 3, "name": "Initech"},
            "department": {"id": 2, "name": "Engineering"},
            "start_date": "2025-02-28",
            "end_date": "May 30, 2025",
            "tasks_count": 12,
            "team": [
                {"id": 3, "name": "Bob Johnson", "initials": "BJ"},
                {"id": 2, "name": "Jane Doe", "initials": "JD"}
            ],
            "image_url": "/static/images/project4.jpg"
        }
    ]
    
    # Sample pagination
    pagination = {
        "current_page": 1,
        "total_pages": 3,
        "has_previous": False,
        "has_next": True,
        "next_page": 2,
        "previous_page": None,
        "page_range": range(1, 4)  # Pages 1 to 3
    }
    
    return templates.TemplateResponse(
        request=request, 
        name="modern_projects.html", 
        context={
            "request": request,
            "stats": stats,
            "clients": clients,
            "departments": departments,
            "users": users,
            "projects": projects,
            "pagination": pagination
        }
    )

@router.get("/{project_id}")
async def project_details(request: Request, project_id: int):
    """Project details page"""
    # Sample project data for demonstration
    project = {
        "id": project_id,
        "name": f"Project {project_id}",
        "description": "This is a detailed description of the project. It outlines the goals, scope, and key deliverables. The project aims to deliver a comprehensive solution that meets all the client requirements.",
        "status": "active",
        "progress": 65,
        "client": {"id": 1, "name": "Acme Corporation"},
        "department": {"name": "Engineering"},
        "start_date": "April 1, 2025",
        "end_date": "May 15, 2025",
        "days_remaining": 14,
        "budget_used": 60,
        "tasks_count": 24,
        "team": [
            {"id": 1, "name": "John Smith", "role": "Project Manager", "initials": "JS"},
            {"id": 2, "name": "Jane Doe", "role": "Lead Developer", "initials": "JD"},
            {"id": 3, "name": "Bob Johnson", "role": "UI/UX Designer", "initials": "BJ"},
            {"id": 4, "name": "Alice Brown", "role": "QA Specialist", "initials": "AB"}
        ],
        "tasks": {
            "upcoming": [
                {
                    "id": 1,
                    "title": "Finalize API documentation",
                    "description": "Complete documentation for all API endpoints",
                    "priority": "high",
                    "due_date": "May 5, 2025",
                    "assignee": "Jane Doe"
                },
                {
                    "id": 2,
                    "title": "User testing session",
                    "description": "Conduct user testing with focus group",
                    "priority": "medium",
                    "due_date": "May 8, 2025",
                    "assignee": "Alice Brown"
                }
            ],
            "completed": [
                {
                    "id": 3,
                    "title": "Database schema design",
                    "description": "Create initial database schema",
                    "completed_date": "April 20, 2025",
                    "assignee": "Bob Johnson"
                },
                {
                    "id": 4,
                    "title": "Frontend prototype",
                    "description": "Develop interactive prototype",
                    "completed_date": "April 25, 2025",
                    "assignee": "Jane Doe"
                }
            ]
        },
        "milestones": [
            {
                "title": "Project Kickoff",
                "description": "Initial meeting with stakeholders",
                "date": "April 1, 2025",
                "status": "completed"
            },
            {
                "title": "Design Phase Complete",
                "description": "Finalize all design assets",
                "date": "April 15, 2025",
                "status": "completed"
            },
            {
                "title": "Development Phase",
                "description": "Complete core functionality",
                "date": "May 5, 2025",
                "status": "current"
            },
            {
                "title": "User Testing",
                "description": "Conduct user testing sessions",
                "date": "May 10, 2025",
                "status": "future"
            },
            {
                "title": "Project Delivery",
                "description": "Final delivery and client handover",
                "date": "May 15, 2025",
                "status": "future"
            }
        ],
        "files": [
            {
                "name": "Project Proposal.pdf",
                "type": "pdf",
                "size": "2.5 MB",
                "uploaded_by": "John Smith",
                "upload_date": "April 1, 2025"
            },
            {
                "name": "Design Mockups.jpg",
                "type": "jpg",
                "size": "8.7 MB",
                "uploaded_by": "Bob Johnson",
                "upload_date": "April 10, 2025"
            },
            {
                "name": "Project Timeline.xlsx",
                "type": "xlsx",
                "size": "1.2 MB",
                "uploaded_by": "John Smith",
                "upload_date": "April 5, 2025"
            },
            {
                "name": "Requirements Document.docx",
                "type": "docx",
                "size": "3.4 MB",
                "uploaded_by": "Jane Doe",
                "upload_date": "April 3, 2025"
            }
        ],
        "comments": [
            {
                "user": "John Smith",
                "text": "I've uploaded the latest project timeline. Please review and let me know if you have any questions.",
                "date": "April 5, 2025"
            },
            {
                "user": "Jane Doe",
                "text": "The backend API is now 80% complete. We're on track to meet our May 5th milestone.",
                "date": "April 22, 2025"
            },
            {
                "user": "Bob Johnson",
                "text": "All design mockups have been finalized and uploaded. Please check the Files section.",
                "date": "April 10, 2025"
            }
        ],
        "image_url": f"/static/images/project{project_id}.jpg" if 1 <= project_id <= 4 else "/static/images/project-placeholder.jpg"
    }
    
    return templates.TemplateResponse(
        request=request, 
        name="modern_project_details.html", 
        context={"request": request, "project": project}
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

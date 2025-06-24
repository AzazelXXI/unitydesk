"""
Project Web Router - Handles project web routes and Jinja template rendering

This module contains all project-related web routes for the CSA Platform, including:
- Project dashboard
- Project details
- Project creation and editing interfaces
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import List, Optional
import logging

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.models.project import Project, ProjectStatusEnum
from src.controllers.project_controller import ProjectController

# Configure logging
logger = logging.getLogger(__name__)

# Create router for project web routes
router = APIRouter(
    tags=["web-projects"], responses={404: {"description": "Page not found"}}
)

# Templates - use absolute path to avoid issues
templates_path = "src/views"
templates = Jinja2Templates(directory=templates_path)


@router.get("/projects", response_class=HTMLResponse)
async def projects_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Display the projects dashboard with all projects
    """
    try:
        print(f"=== PROJECTS DASHBOARD ACCESS ===")
        print(f"User: {current_user.name} (ID: {current_user.id})")
        print(f"User Type: {current_user.user_type}")

        # Get success message from query parameter (remove this since we don't need it)
        # success_message = request.query_params.get("success")

        # Query all projects with basic statistics
        projects_query = text(
            """
            SELECT 
                p.id,
                p.name,
                p.description,
                p.status,
                p.progress,
                p.budget,
                p.start_date,
                p.end_date,
                p.created_at,
                p.updated_at,
                COUNT(t.id) as task_count,
                COUNT(CASE WHEN t.status = 'COMPLETED' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            GROUP BY p.id, p.name, p.description, p.status, p.progress, p.budget, 
                     p.start_date, p.end_date, p.created_at, p.updated_at
            ORDER BY p.created_at DESC
        """
        )

        result = await db.execute(projects_query)
        project_rows = result.fetchall()

        print(f"Found {len(project_rows)} projects in database")

        # Convert to project objects
        projects = []
        for row in project_rows:
            project = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "status": row.status,
                "progress": row.progress,
                "budget": float(row.budget) if row.budget else 0,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "task_count": row.task_count or 0,
                "completed_tasks": row.completed_tasks or 0,
                "completion_percentage": round(
                    (
                        (row.completed_tasks / row.task_count * 100)
                        if row.task_count > 0
                        else 0
                    ),
                    1,
                ),
            }
            projects.append(project)

        # Calculate project statistics
        stats = {
            "total": len(projects),
            "planning": len([p for p in projects if p["status"] == "Planning"]),
            "in_progress": len([p for p in projects if p["status"] == "In Progress"]),
            "completed": len([p for p in projects if p["status"] == "Completed"]),
            "canceled": len([p for p in projects if p["status"] == "Canceled"]),
            "total_budget": sum([p["budget"] for p in projects]),
            "avg_progress": round(
                (
                    sum([p["progress"] for p in projects]) / len(projects)
                    if projects
                    else 0
                ),
                1,
            ),
        }

        print(f"📊 Project Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Planning: {stats['planning']}")
        print(f"  In Progress: {stats['in_progress']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Average Progress: {stats['avg_progress']}%")

        return templates.TemplateResponse(
            "project/templates/projects.html",
            {
                "request": request,
                "current_user": current_user,
                "projects": projects,
                "stats": stats,
                "page_title": "Projects Dashboard",
            },
        )

    except Exception as e:
        print(f"ERROR in projects dashboard: {str(e)}")
        logger.error(f"Error loading projects dashboard: {str(e)}", exc_info=True)

        return templates.TemplateResponse(
            "project/templates/projects.html",
            {
                "request": request,
                "current_user": current_user,
                "projects": [],
                "stats": {
                    "total": 0,
                    "planning": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "canceled": 0,
                    "total_budget": 0,
                    "avg_progress": 0,
                },
                "error": f"Could not load projects: {str(e)}",
                "page_title": "Projects Dashboard",
            },
        )


@router.get("/projects/new", response_class=HTMLResponse)
async def new_project(
    request: Request,
    current_user: User = Depends(get_current_user_web),
):
    """
    Display new project creation form
    """
    return templates.TemplateResponse(
        "project/templates/new_project.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Create New Project",
        },
    )


@router.post("/projects/new", response_class=HTMLResponse)
async def create_project_web(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Handle project creation form submission
    """
    try:
        form_data = await request.form()

        # Create project data from form
        project_data = {
            "name": form_data.get("name"),
            "description": form_data.get("description"),
            "client_name": form_data.get("client_name"),
            "status": form_data.get("status", "Planning"),
            "priority": form_data.get("priority", "Medium"),
            "budget": (
                float(form_data.get("budget", 0)) if form_data.get("budget") else None
            ),
            "start_date": (
                form_data.get("start_date") if form_data.get("start_date") else None
            ),
            "end_date": (
                form_data.get("end_date") if form_data.get("end_date") else None
            ),
            "department": form_data.get("department"),
            "project_manager": form_data.get("project_manager"),
            "goals": form_data.get("goals"),
        }  # Use the ProjectController to create the project
        from src.controllers.project_controller import ProjectController

        new_project = await ProjectController.create_project(
            project_data, db, current_user.id
        )

        print(f"Project created successfully with ID: {new_project.id}")

        # Set a flag in session storage to show success modal
        # We'll use a redirect with a hash fragment to trigger the modal
        return RedirectResponse(
            url="/projects#project-created",
            status_code=303,
        )

    except Exception as e:
        print(f"Error creating project: {e}")
        # Return to form with error
        return templates.TemplateResponse(
            "project/templates/new_project.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Create New Project",
                "error": f"Failed to create project: {str(e)}",
            },
        )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_details(
    request: Request,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Display project details page
    """
    try:
        print(f"=== PROJECT DETAILS ACCESS ===")
        print(f"Project ID: {project_id}")
        print(f"User: {current_user.name} (ID: {current_user.id})")

        # Get project with related data
        project_query = text(
            """
            SELECT 
                p.id,
                p.name,
                p.description,
                p.status,
                p.progress,
                p.budget,
                p.start_date,
                p.end_date,
                p.created_at,
                p.updated_at,
                COUNT(t.id) as task_count,
                COUNT(CASE WHEN t.status = 'COMPLETED' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN t.status = 'IN_PROGRESS' THEN 1 END) as active_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE p.id = :project_id
            GROUP BY p.id, p.name, p.description, p.status, p.progress, p.budget,                     p.start_date, p.end_date, p.created_at, p.updated_at        """
        )

        result = await db.execute(project_query, {"project_id": project_id})
        project_row = result.fetchone()

        print(f"Query executed. Found project: {project_row is not None}")

        if not project_row:
            raise HTTPException(status_code=404, detail="Project not found")

        # Map project status to template stages
        status_to_stage = {
            "Planning": "planning",
            "In Progress": "execution",
            "Completed": "evaluation",
            "On Hold": "monitoring",
            "Cancelled": "planning",
        }
        current_stage = status_to_stage.get(project_row.status, "planning")

        project = {
            "id": project_row.id,
            "name": project_row.name,
            "description": project_row.description,
            "status": project_row.status,
            "progress": project_row.progress,
            "budget": float(project_row.budget) if project_row.budget else 0,
            "start_date": project_row.start_date,
            "end_date": project_row.end_date,
            "created_at": project_row.created_at,
            "updated_at": project_row.updated_at,
            "task_count": project_row.task_count or 0,
            "completed_tasks": project_row.completed_tasks or 0,
            "active_tasks": project_row.active_tasks
            or 0,  # Add missing fields with defaults for template compatibility
            "project_type": "General",  # Default project type
            "client": None,  # No client data available
            "target_end_date": project_row.end_date,  # Use end_date as target
            "current_stage": current_stage,  # Use mapped stage
            "workflow_progress": project_row.progress
            or 0,  # Use progress as workflow progress
            "client_brief": None,  # No client brief available
        }

        # Get project tasks
        tasks_query = text(
            """
            SELECT 
                t.id,
                t.name,
                t.description,
                t.status,
                t.priority,
                t.start_date,
                t.due_date,
                t.completed_date,
                u.name as assignee_name
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            WHERE t.project_id = :project_id
            ORDER BY t.created_at DESC
        """
        )

        tasks_result = await db.execute(tasks_query, {"project_id": project_id})
        task_rows = tasks_result.fetchall()

        tasks = []
        for row in task_rows:
            task = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "status": row.status,
                "priority": row.priority,
                "start_date": row.start_date,
                "due_date": row.due_date,
                "completed_date": row.completed_date,
                "assignee_name": row.assignee_name,
            }
            tasks.append(task)

        return templates.TemplateResponse(
            "project/templates/project_details.html",
            {
                "request": request,
                "current_user": current_user,
                "project": project,
                "tasks": tasks,
                "page_title": f"Project: {project['name']}",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading project details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load project details")

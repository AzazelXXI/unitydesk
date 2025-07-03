from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from fastapi import status, APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import List, Optional
import logging
from datetime import datetime
import json
from src.models.user import User
from src.models.project import Project, ProjectStatusEnum
from src.models.task import Task, TaskStatusEnum, TaskPriorityEnum
from src.models.association_tables import task_assignees
from src.models.activity import ActivityType
from src.controllers.project_controller import ProjectController
from src.services.activity_service import ActivityService
from src.services.project_status_service import ProjectStatusService

router = APIRouter(
    tags=["web-projects"], responses={404: {"description": "Page not found"}}
)


@router.put("/projects/{project_id}/members/{user_id}")
async def update_project_member(
    project_id: int,
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Update a member in a project"""
    try:
        # Check permissions
        project = await db.execute(select(Project).where(Project.id == project_id))
        project = project.scalar_one_or_none()
        if not project:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Project not found"},
            )

        if not (
            current_user.user_type in ["system_admin", "project_manager"]
            or project.owner_id == current_user.id
        ):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Insufficient permissions"},
            )

        # Check membership
        member_query = text(
            "SELECT * FROM project_members WHERE project_id = :project_id AND user_id = :user_id"
        )
        member_result = await db.execute(
            member_query, {"project_id": project_id, "user_id": user_id}
        )
        if not member_result.fetchone():
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Member not found in project"},
            )

        # Log activity
        try:
            await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=current_user.id,
                activity_type=ActivityType.MEMBER_UPDATED,
                description=f"{current_user.name} updated member {user_id}",
                target_entity_type="user",
                target_entity_id=user_id,
            )
        except Exception as e:
            logger.warning(f"Failed to log member update: {str(e)}")

        return JSONResponse(
            status_code=200, content={"success": True, "message": "Member updated"}
        )

    except Exception as e:
        logger.error(f"Error updating project member: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error"},
        )


# --- Project Member Remove ---
@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Remove a member from a project"""
    try:
        # Check permissions
        project = await db.execute(select(Project).where(Project.id == project_id))
        project = project.scalar_one_or_none()
        if not project:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Project not found"},
            )
        if not (
            current_user.user_type in ["system_admin", "project_manager"]
            or project.owner_id == current_user.id
        ):
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Insufficient permissions"},
            )

        # Check membership
        member_query = text(
            "SELECT * FROM project_members WHERE project_id = :project_id AND user_id = :user_id"
        )
        member_result = await db.execute(
            member_query, {"project_id": project_id, "user_id": user_id}
        )
        if not member_result.fetchone():
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Member not found in project"},
            )

        # Remove member
        delete_query = text(
            "DELETE FROM project_members WHERE project_id = :project_id AND user_id = :user_id"
        )
        await db.execute(delete_query, {"project_id": project_id, "user_id": user_id})
        await db.commit()

        # Log activity
        try:
            await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=current_user.id,
                activity_type=ActivityType.MEMBER_REMOVED,
                description=f"{current_user.name} removed user {user_id} from the project",
                target_entity_type="user",
                target_entity_id=user_id,
                activity_data={},
            )
        except Exception as e:
            logger.warning(f"Failed to log member removal: {str(e)}")

        return JSONResponse(
            status_code=200, content={"success": True, "message": "Member removed"}
        )
    except Exception as e:
        logger.error(f"Error removing member: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to remove member"},
        )


"""
Project Web Router - Handles project web routes and Jinja template rendering

This module contains all project-related web routes for the CSA Platform, including:
- Project dashboard
- Project details
- Project creation and editing interfaces
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import List, Optional
import logging
from datetime import datetime
import json

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.models.project import Project, ProjectStatusEnum
from src.models.task import Task, TaskStatusEnum, TaskPriorityEnum
from src.models.association_tables import task_assignees
from src.models.activity import ActivityType
from src.controllers.project_controller import ProjectController
from src.services.activity_service import ActivityService
from src.services.project_status_service import ProjectStatusService

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
    status: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    search: Optional[str] = None,
    progress_min: Optional[int] = None,
    progress_max: Optional[int] = None,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
):
    """
    Display the projects dashboard with filtering and sorting
    """
    try:
        print(f"=== PROJECTS DASHBOARD ACCESS ===")
        print(f"User: {current_user.name} (ID: {current_user.id})")
        print(f"Filters: status={status}, sort_by={sort_by}, sort_order={sort_order}")
        print(
            f"Search: {search}, progress: {progress_min}-{progress_max}, budget: {budget_min}-{budget_max}"
        )

        # Build dynamic WHERE clause
        where_conditions = []
        params = {}

        if status and status != "all":
            where_conditions.append("p.status = :status")
            params["status"] = status

        if search:
            where_conditions.append(
                "(p.name ILIKE :search OR p.description ILIKE :search)"
            )
            params["search"] = f"%{search}%"

        if progress_min is not None:
            where_conditions.append("p.progress >= :progress_min")
            params["progress_min"] = progress_min

        if progress_max is not None:
            where_conditions.append("p.progress <= :progress_max")
            params["progress_max"] = progress_max

        if budget_min is not None:
            where_conditions.append("p.budget >= :budget_min")
            params["budget_min"] = budget_min

        if budget_max is not None:
            where_conditions.append("p.budget <= :budget_max")
            params["budget_max"] = budget_max

        where_clause = (
            "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        )

        # Build ORDER BY clause
        valid_sort_fields = {
            "name": "p.name",
            "created_at": "p.created_at",
            "start_date": "p.start_date",
            "end_date": "p.end_date",
            "progress": "p.progress",
            "budget": "p.budget",
            "status": "p.status",
        }

        sort_field = valid_sort_fields.get(sort_by, "p.created_at")
        sort_direction = "ASC" if sort_order == "asc" else "DESC"
        order_clause = f"ORDER BY {sort_field} {sort_direction}"

        # Query projects with filtering and sorting
        projects_query = text(
            f"""
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
            {where_clause}
            GROUP BY p.id, p.name, p.description, p.status, p.progress, p.budget, 
                     p.start_date, p.end_date, p.created_at, p.updated_at
            {order_clause}
        """
        )

        result = await db.execute(projects_query, params)
        project_rows = result.fetchall()

        print(f"Found {len(project_rows)} projects after filtering")

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
                # Filter parameters for maintaining state
                "current_status": status or "all",
                "current_sort_by": sort_by,
                "current_sort_order": sort_order,
                "current_search": search or "",
                "current_progress_min": progress_min,
                "current_progress_max": progress_max,
                "current_budget_min": budget_min,
                "current_budget_max": budget_max,
                # Available options for dropdowns
                "status_options": [
                    {"value": "all", "label": "All Statuses"},
                    {"value": "PLANNING", "label": "Planning"},
                    {"value": "IN_PROGRESS", "label": "In Progress"},
                    {"value": "COMPLETED", "label": "Completed"},
                    {"value": "ON_HOLD", "label": "On Hold"},
                    {"value": "CANCELED", "label": "Canceled"},
                ],
                "sort_options": [
                    {"value": "created_at", "label": "Date Created"},
                    {"value": "name", "label": "Project Name"},
                    {"value": "start_date", "label": "Start Date"},
                    {"value": "end_date", "label": "End Date"},
                    {"value": "progress", "label": "Progress"},
                    {"value": "budget", "label": "Budget"},
                    {"value": "status", "label": "Status"},
                ],
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Display new project creation form
    """
    try:
        # Get all available project statuses (default + custom)
        from src.services.project_status_service import ProjectStatusService

        project_statuses = await ProjectStatusService.get_all_project_statuses(db)

    except Exception as e:
        logger.error(f"Error fetching project statuses: {str(e)}")
        # Fallback to default statuses
        from src.models.project import DEFAULT_PROJECT_STATUSES

        project_statuses = [
            {
                "status_name": status,
                "display_name": status,
                "color": "#6c757d",
                "is_custom": False,
                "description": f"Default {status} status",
            }
            for status in DEFAULT_PROJECT_STATUSES
        ]

    return templates.TemplateResponse(
        "project/templates/new_project.html",
        {
            "request": request,
            "current_user": current_user,
            "project_statuses": project_statuses,
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
    # Task filtering parameters
    task_status: Optional[str] = None,
    task_priority: Optional[str] = None,
    task_search: Optional[str] = None,
    task_sort_by: Optional[str] = "created_at",
    task_sort_order: Optional[str] = "desc",
    task_assignee: Optional[str] = None,
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

        # Get project tasks with filtering
        print(
            f"Task filters: status={task_status}, priority={task_priority}, search={task_search}"
        )
        print(
            f"Task sorting: {task_sort_by} {task_sort_order}, assignee={task_assignee}"
        )

        # Build task WHERE clause
        task_where_conditions = ["t.project_id = :project_id"]
        task_params = {"project_id": project_id}

        if task_status and task_status != "all":
            task_where_conditions.append("t.status = :task_status")
            task_params["task_status"] = task_status.upper()

        if task_priority and task_priority != "all":
            task_where_conditions.append("t.priority = :task_priority")
            task_params["task_priority"] = task_priority.upper()

        if task_search:
            task_where_conditions.append(
                "(t.name ILIKE :task_search OR t.description ILIKE :task_search)"
            )
            task_params["task_search"] = f"%{task_search}%"

        if task_assignee and task_assignee != "all":
            if task_assignee == "unassigned":
                task_where_conditions.append("ta.user_id IS NULL")
            else:
                task_where_conditions.append("ta.user_id = :task_assignee")
                task_params["task_assignee"] = int(task_assignee)

        task_where_clause = " AND ".join(task_where_conditions)

        # Build task ORDER BY clause
        valid_task_sort_fields = {
            "name": "t.name",
            "created_at": "t.created_at",
            "due_date": "t.due_date",
            "priority": "t.priority",
            "status": "t.status",
            "assignee": "u.name",
        }

        task_sort_field = valid_task_sort_fields.get(task_sort_by, "t.created_at")
        task_sort_direction = "ASC" if task_sort_order == "asc" else "DESC"
        task_order_clause = f"ORDER BY {task_sort_field} {task_sort_direction}"

        tasks_query = text(
            f"""
            SELECT 
                t.id,
                t.name,
                t.description,
                t.status,
                t.priority,
                t.start_date,
                t.due_date,
                t.completed_date,
                t.created_at,
                STRING_AGG(u.name, ', ') as assignee_names,
                STRING_AGG(CAST(u.id AS TEXT), ',') as assignee_ids
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            WHERE {task_where_clause}
            GROUP BY t.id, t.name, t.description, t.status, t.priority, t.start_date, t.due_date, t.completed_date, t.created_at
            {task_order_clause}
        """
        )

        tasks_result = await db.execute(tasks_query, task_params)
        task_rows = tasks_result.fetchall()

        print(f"Found {len(task_rows)} tasks after filtering")

        tasks = []
        for row in task_rows:
            # Process assignee data
            assignee_names = []
            assignee_ids = []
            if row.assignee_names:
                assignee_names = [
                    name.strip() for name in row.assignee_names.split(",")
                ]
            if row.assignee_ids:
                assignee_ids = [
                    int(id_str.strip())
                    for id_str in row.assignee_ids.split(",")
                    if id_str.strip()
                ]

            task = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "status": row.status,
                "priority": row.priority,
                "start_date": row.start_date,
                "due_date": row.due_date,
                "completed_date": row.completed_date,
                "created_at": row.created_at,
                "assignee_names": assignee_names,
                "assignee_ids": assignee_ids,
                # For backward compatibility
                "assignee_name": assignee_names[0] if assignee_names else None,
                "assignee_id": assignee_ids[0] if assignee_ids else None,
            }
            tasks.append(task)

        # Get users for task assignment
        users_query = text(
            """
            SELECT id, name, email
            FROM users
            ORDER BY name
        """
        )
        users_result = await db.execute(users_query)
        user_rows = users_result.fetchall()

        users = []
        for row in user_rows:
            users.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "email": row.email,
                }
            )

        # Get recent activities for the project (increased limit for better activity log)
        activities = await ActivityService.get_recent_activities(
            db, project_id, limit=50
        )

        # Get project members with their task counts
        members_query = text(
            """
            SELECT 
                u.id,
                u.name,
                u.email,
                pm.joined_at,
                COUNT(DISTINCT ta.task_id) as total_tasks,
                COUNT(DISTINCT CASE WHEN t.status = 'COMPLETED' THEN ta.task_id END) as completed_tasks
            FROM users u
            JOIN project_members pm ON u.id = pm.user_id
            LEFT JOIN task_assignees ta ON u.id = ta.user_id
            LEFT JOIN tasks t ON ta.task_id = t.id AND t.project_id = :project_id
            WHERE pm.project_id = :project_id
            GROUP BY u.id, u.name, u.email, pm.joined_at
            ORDER BY pm.joined_at ASC
        """
        )

        members_result = await db.execute(members_query, {"project_id": project_id})
        member_rows = members_result.fetchall()

        members = []
        for row in member_rows:
            member = {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "joined_at": row.joined_at,
                "total_tasks": row.total_tasks or 0,
                "completed_tasks": row.completed_tasks or 0,
            }
            members.append(member)

        # Get project files/attachments
        files_query = text(
            """
            SELECT 
                a.id,
                a.file_name,
                a.file_size,
                a.mime_type,
                a.created_at,
                u.name as uploader_name,
                u.id as uploader_id
            FROM attachments a
            JOIN users u ON a.uploader_id = u.id
            WHERE a.project_id = :project_id
            ORDER BY a.created_at DESC
        """
        )

        files_result = await db.execute(files_query, {"project_id": project_id})
        file_rows = files_result.fetchall()

        files = []
        for row in file_rows:
            # Determine file type and icon based on mime_type
            file_type = "Document"
            file_icon = "bi-file-earmark"
            file_color = "text-secondary"

            if row.mime_type:
                if row.mime_type.startswith("image/"):
                    file_type = "Image"
                    file_icon = "bi-file-earmark-image"
                    file_color = "text-success"
                elif row.mime_type == "application/pdf":
                    file_type = "PDF"
                    file_icon = "bi-file-earmark-pdf"
                    file_color = "text-danger"
                elif row.mime_type in [
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ]:
                    file_type = "Document"
                    file_icon = "bi-file-earmark-word"
                    file_color = "text-primary"
                elif row.mime_type in [
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ]:
                    file_type = "Spreadsheet"
                    file_icon = "bi-file-earmark-excel"
                    file_color = "text-success"
                elif row.mime_type.startswith("video/"):
                    file_type = "Video"
                    file_icon = "bi-file-earmark-play"
                    file_color = "text-info"
                elif row.mime_type.startswith("audio/"):
                    file_type = "Audio"
                    file_icon = "bi-file-earmark-music"
                    file_color = "text-warning"

            # Format file size
            file_size_formatted = "Unknown"
            if row.file_size:
                if row.file_size < 1024:
                    file_size_formatted = f"{row.file_size} B"
                elif row.file_size < 1024 * 1024:
                    file_size_formatted = f"{row.file_size / 1024:.1f} KB"
                else:
                    file_size_formatted = f"{row.file_size / (1024 * 1024):.1f} MB"

            file_data = {
                "id": row.id,
                "file_name": row.file_name,
                "file_type": file_type,
                "file_icon": file_icon,
                "file_color": file_color,
                "file_size": file_size_formatted,
                "uploader_name": row.uploader_name,
                "uploader_id": row.uploader_id,
                "created_at": row.created_at,
            }
            files.append(file_data)

        return templates.TemplateResponse(
            "project/templates/project_details.html",
            {
                "request": request,
                "current_user": current_user,
                "project": project,
                "tasks": tasks,
                "users": users,
                "activities": activities,
                "members": members,
                "files": files,
                "page_title": f"Project: {project['name']}",
                # Task filter parameters
                "current_task_status": task_status or "all",
                "current_task_priority": task_priority or "all",
                "current_task_search": task_search or "",
                "current_task_sort_by": task_sort_by,
                "current_task_sort_order": task_sort_order,
                "current_task_assignee": task_assignee or "all",
                # Task filter options
                "task_status_options": [
                    {"value": "all", "label": "All Statuses"},
                    {"value": "NOT_STARTED", "label": "Not Started"},
                    {"value": "IN_PROGRESS", "label": "In Progress"},
                    {"value": "BLOCKED", "label": "Blocked"},
                    {"value": "COMPLETED", "label": "Completed"},
                ],
                "task_priority_options": [
                    {"value": "all", "label": "All Priorities"},
                    {"value": "LOW", "label": "Low"},
                    {"value": "MEDIUM", "label": "Medium"},
                    {"value": "HIGH", "label": "High"},
                    {"value": "URGENT", "label": "Urgent"},
                ],
                "task_sort_options": [
                    {"value": "created_at", "label": "Date Created"},
                    {"value": "name", "label": "Task Name"},
                    {"value": "due_date", "label": "Due Date"},
                    {"value": "priority", "label": "Priority"},
                    {"value": "status", "label": "Status"},
                    {"value": "assignee", "label": "Assignee"},
                ],
                "task_assignee_options": [
                    {"value": "all", "label": "All Assignees"},
                    {"value": "unassigned", "label": "Unassigned"},
                ]
                + [{"value": str(user["id"]), "label": user["name"]} for user in users],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading project details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load project details")


@router.post("/projects/{project_id}/tasks")
async def create_task(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Create a new task for a project"""
    try:
        # Get the raw form data for debugging
        form = await request.form()
        logger.info(f"Raw form data received: {dict(form)}")

        # Extract form fields manually
        taskName = form.get("taskName")
        taskDescription = form.get("taskDescription", "")
        taskPriority = form.get("taskPriority", "Medium")
        taskStatus = form.get("taskStatus", "Not Started")
        taskAssignees = form.getlist("taskAssignees")  # Get list of assignees
        taskStartDate = form.get("taskStartDate")
        taskDueDate = form.get("taskDueDate")
        taskEstimatedHours = form.get("taskEstimatedHours")

        # Validate required fields
        if not taskName:
            raise HTTPException(status_code=422, detail="Task name is required")

        # Debug logging
        logger.info(
            f"Creating task with data: name={taskName}, priority={taskPriority}, status={taskStatus}, assignees={taskAssignees}"
        )

        # Convert string values to enums
        try:
            priority_enum = TaskPriorityEnum(taskPriority)
            status_enum = TaskStatusEnum(taskStatus)
        except ValueError as e:
            logger.error(f"Invalid enum value: {e}")
            raise HTTPException(
                status_code=422, detail=f"Invalid priority or status value: {e}"
            )

        # Convert assignees to int list if provided
        assignee_ids = []
        if taskAssignees:
            for assignee in taskAssignees:
                if assignee and assignee.strip():
                    try:
                        assignee_ids.append(int(assignee))
                    except ValueError:
                        raise HTTPException(
                            status_code=422, detail=f"Invalid assignee ID: {assignee}"
                        )

        # Convert estimated hours to int if provided
        estimated_hours = None
        if taskEstimatedHours and taskEstimatedHours.strip():
            try:
                estimated_hours = int(taskEstimatedHours)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid estimated hours")

        # Verify project exists and user has access
        project_query = text("SELECT id FROM projects WHERE id = :project_id")
        project_result = await db.execute(project_query, {"project_id": project_id})
        if not project_result.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Parse dates if provided
        start_date = None
        due_date = None
        if taskStartDate and taskStartDate.strip():
            try:
                start_date = datetime.strptime(taskStartDate, "%Y-%m-%d")
            except ValueError:
                pass
        if taskDueDate and taskDueDate.strip():
            try:
                due_date = datetime.strptime(taskDueDate, "%Y-%m-%d")
            except ValueError:
                pass

        # Create the task
        new_task = Task(
            name=taskName,
            description=taskDescription if taskDescription else None,
            project_id=project_id,
            status=status_enum,
            priority=priority_enum,
            estimated_hours=estimated_hours,
            start_date=start_date,
            due_date=due_date,
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        # Assign users if specified
        if assignee_ids:
            for assignee_id in assignee_ids:
                # Verify user exists
                user_query = text("SELECT id FROM users WHERE id = :user_id")
                user_result = await db.execute(user_query, {"user_id": assignee_id})
                if user_result.fetchone():
                    # Insert into task_assignees table
                    assign_query = text(
                        """
                        INSERT INTO task_assignees (task_id, user_id, assigned_at)
                        VALUES (:task_id, :user_id, :assigned_at)
                    """
                    )
                    await db.execute(
                        assign_query,
                        {
                            "task_id": new_task.id,
                            "user_id": assignee_id,
                            "assigned_at": datetime.utcnow(),
                        },
                    )
                else:
                    logger.warning(f"User {assignee_id} not found, skipping assignment")

            await db.commit()

        logger.info(
            f"Task {new_task.id} created by user {current_user.id} in project {project_id}"
        )

        # Log activity
        try:
            description = ActivityService.create_task_activity_description(
                "created", new_task.name, current_user.name
            )
            await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=current_user.id,
                activity_type=ActivityType.TASK_CREATED,
                description=description,
                target_entity_type="task",
                target_entity_id=new_task.id,
                activity_data={
                    "task_name": new_task.name,
                    "task_priority": (
                        new_task.priority.value if new_task.priority else None
                    ),
                    "task_status": new_task.status.value if new_task.status else None,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log task creation activity: {str(e)}")

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Task created successfully",
                "task": {
                    "id": new_task.id,
                    "name": new_task.name,
                    "description": new_task.description,
                    "status": (
                        new_task.status.value if new_task.status else "NOT_STARTED"
                    ),
                    "priority": (
                        new_task.priority.value if new_task.priority else "MEDIUM"
                    ),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to create task"},
        )


@router.post("/projects/{project_id}/members")
async def add_project_member(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Add a new member to a project"""
    try:
        # Get the request body
        body = await request.json()
        user_id = body.get("user_id")

        # Validate required fields
        if not user_id:
            raise HTTPException(status_code=422, detail="User ID is required")

        # Convert user_id to int
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid user ID")

        # Verify project exists
        project_query = text("SELECT id FROM projects WHERE id = :project_id")
        project_result = await db.execute(project_query, {"project_id": project_id})
        if not project_result.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify user exists
        user_query = text("SELECT id, name, email FROM users WHERE id = :user_id")
        user_result = await db.execute(user_query, {"user_id": user_id})
        user_row = user_result.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user is already a member of this project
        existing_member_query = text(
            "SELECT project_id FROM project_members WHERE project_id = :project_id AND user_id = :user_id"
        )
        existing_result = await db.execute(
            existing_member_query, {"project_id": project_id, "user_id": user_id}
        )
        if existing_result.fetchone():
            raise HTTPException(
                status_code=409, detail="User is already a member of this project"
            )

        # Add the member to the project
        insert_member_query = text(
            """
            INSERT INTO project_members (project_id, user_id, joined_at)
            VALUES (:project_id, :user_id, :joined_at)
            """
        )

        await db.execute(
            insert_member_query,
            {
                "project_id": project_id,
                "user_id": user_id,
                "joined_at": datetime.utcnow(),
            },
        )
        await db.commit()

        logger.info(
            f"User {user_id} added to project {project_id} by user {current_user.id}"
        )

        # Log activity
        try:
            description = f"{current_user.name} added {user_row.name} to the project"
            await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=current_user.id,
                activity_type=ActivityType.MEMBER_ADDED,
                description=description,
                target_entity_type="user",
                target_entity_id=user_id,
                activity_data={
                    "user_name": user_row.name,
                    "user_email": user_row.email,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log member addition activity: {str(e)}")

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Member added successfully",
                "member": {
                    "user_id": user_id,
                    "name": user_row.name,
                    "email": user_row.email,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding project member: {str(e)}", exc_info=True)
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Failed to add member"},
        )


# =============================================================================
# Project-Specific Custom Status Management Routes
# =============================================================================


@router.get("/api/projects/{project_id}/statuses", response_class=JSONResponse)
async def get_project_statuses(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Get all statuses for a specific project (default + custom)"""
    try:
        statuses = await ProjectStatusService.get_project_statuses(db, project_id)
        return {"success": True, "data": statuses, "count": len(statuses)}
    except Exception as e:
        logger.error(f"Error getting statuses for project {project_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/api/projects/{project_id}/statuses", response_class=JSONResponse)
async def create_project_custom_status(
    project_id: int,
    status_name: str = Form(...),
    display_name: str = Form(...),
    description: Optional[str] = Form(None),
    color: str = Form("#007bff"),
    is_final: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Create a new custom status for a specific project"""
    try:
        # Check if user has permission to manage this project
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check permissions: owner, admin, or project manager
        if not (
            current_user.user_type in ["system_admin", "project_manager"]
            or project.owner_id == current_user.id
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        custom_status = await ProjectStatusService.create_custom_project_status(
            db=db,
            project_id=project_id,
            status_name=status_name,
            display_name=display_name,
            description=description,
            color=color,
            is_final=is_final,
        )

        return {
            "success": True,
            "data": {
                "id": custom_status.id,
                "status_name": custom_status.status_name,
                "display_name": custom_status.display_name,
                "color": custom_status.color,
                "description": custom_status.description,
                "is_final": custom_status.is_final,
                "project_id": custom_status.project_id,
            },
            "message": f"Custom status '{custom_status.display_name}' created for this project",
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom status for project {project_id}: {str(e)}")
        return {"success": False, "error": "Failed to create custom status"}


@router.put(
    "/api/projects/{project_id}/statuses/{status_id}", response_class=JSONResponse
)
async def update_project_custom_status(
    project_id: int,
    status_id: int,
    display_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    is_final: Optional[bool] = Form(None),
    is_active: Optional[bool] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Update a custom status for a specific project"""
    try:
        # Check permissions
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not (
            current_user.user_type in ["system_admin", "project_manager"]
            or project.owner_id == current_user.id
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        custom_status = await ProjectStatusService.update_custom_project_status(
            db=db,
            status_id=status_id,
            project_id=project_id,
            display_name=display_name,
            description=description,
            color=color,
            is_final=is_final,
            is_active=is_active,
        )

        return {
            "success": True,
            "data": {
                "id": custom_status.id,
                "status_name": custom_status.status_name,
                "display_name": custom_status.display_name,
                "color": custom_status.color,
                "description": custom_status.description,
                "is_final": custom_status.is_final,
            },
            "message": f"Status '{custom_status.display_name}' updated successfully",
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating custom status {status_id} for project {project_id}: {str(e)}"
        )
        return {"success": False, "error": "Failed to update custom status"}


@router.delete(
    "/api/projects/{project_id}/statuses/{status_id}", response_class=JSONResponse
)
async def delete_project_custom_status(
    project_id: int,
    status_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Delete a custom status for a specific project"""
    try:
        # Check permissions
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not (
            current_user.user_type in ["system_admin", "project_manager"]
            or project.owner_id == current_user.id
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        was_deleted = await ProjectStatusService.delete_custom_project_status(
            db=db, status_id=status_id, project_id=project_id
        )

        return {
            "success": True,
            "deleted": was_deleted,
            "message": (
                "Status deleted successfully"
                if was_deleted
                else "Status deactivated (was in use)"
            ),
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting custom status {status_id} for project {project_id}: {str(e)}"
        )
        return {"success": False, "error": "Failed to delete custom status"}


@router.get("/projects/manage-statuses", response_class=HTMLResponse)
async def manage_project_statuses(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Display project status management page
    """
    try:
        # Only allow admins and project managers
        if current_user.user_type not in ["system_admin", "project_manager"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to manage project statuses",
            )

        # Get all available project statuses (default + custom)
        project_statuses = await ProjectStatusService.get_all_project_statuses(db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project statuses for management: {str(e)}")
        # Fallback to default statuses
        from src.models.project import DEFAULT_PROJECT_STATUSES

        project_statuses = [
            {
                "status_name": status,
                "display_name": status,
                "color": "#6c757d",
                "is_custom": False,
                "description": f"Default {status} status",
                "is_final": status in ["Completed", "Canceled"],
                "id": None,
            }
            for status in DEFAULT_PROJECT_STATUSES
        ]

    return templates.TemplateResponse(
        "project/templates/manage_project_statuses.html",
        {
            "request": request,
            "current_user": current_user,
            "project_statuses": project_statuses,
            "page_title": "Manage Project Statuses",
        },
    )

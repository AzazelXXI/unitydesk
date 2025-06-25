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

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.models.project import Project, ProjectStatusEnum
from src.models.task import Task, TaskStatusEnum, TaskPriorityEnum
from src.models.association_tables import task_assignees
from src.models.activity import ActivityType
from src.controllers.project_controller import ProjectController
from src.services.activity_service import ActivityService

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
        print(f"Task filters: status={task_status}, priority={task_priority}, search={task_search}")
        print(f"Task sorting: {task_sort_by} {task_sort_order}, assignee={task_assignee}")
        
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
                u.name as assignee_name,
                u.id as assignee_id
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            WHERE {task_where_clause}
            {task_order_clause}
        """
        )

        tasks_result = await db.execute(tasks_query, task_params)
        task_rows = tasks_result.fetchall()

        print(f"Found {len(task_rows)} tasks after filtering")

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
                "created_at": row.created_at,
                "assignee_name": row.assignee_name,
                "assignee_id": row.assignee_id,
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

        # Get recent activities for the project
        activities = await ActivityService.get_recent_activities(
            db, project_id, limit=5
        )

        return templates.TemplateResponse(
            "project/templates/project_details.html",
            {
                "request": request,
                "current_user": current_user,
                "project": project,
                "tasks": tasks,
                "users": users,
                "activities": activities,
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
                ] + [{"value": str(user["id"]), "label": user["name"]} for user in users],
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
    taskName: str = Form(...),
    taskDescription: Optional[str] = Form(None),
    taskPriority: TaskPriorityEnum = Form(TaskPriorityEnum.MEDIUM),
    taskStatus: TaskStatusEnum = Form(TaskStatusEnum.NOT_STARTED),
    taskAssignee: Optional[int] = Form(None),
    taskStartDate: Optional[str] = Form(None),
    taskDueDate: Optional[str] = Form(None),
    taskEstimatedHours: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """Create a new task for a project"""
    try:
        # Verify project exists and user has access
        project_query = text("SELECT id FROM projects WHERE id = :project_id")
        project_result = await db.execute(project_query, {"project_id": project_id})
        if not project_result.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Parse dates if provided
        start_date = None
        due_date = None
        if taskStartDate:
            try:
                start_date = datetime.strptime(taskStartDate, "%Y-%m-%d")
            except ValueError:
                pass
        if taskDueDate:
            try:
                due_date = datetime.strptime(taskDueDate, "%Y-%m-%d")
            except ValueError:
                pass

        # Create the task
        new_task = Task(
            name=taskName,
            description=taskDescription,
            project_id=project_id,
            status=taskStatus,
            priority=taskPriority,
            estimated_hours=taskEstimatedHours,
            start_date=start_date,
            due_date=due_date,
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        # Assign user if specified
        if taskAssignee:
            # Verify user exists
            user_query = text("SELECT id FROM users WHERE id = :user_id")
            user_result = await db.execute(user_query, {"user_id": taskAssignee})
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
                        "user_id": taskAssignee,
                        "assigned_at": datetime.utcnow(),
                    },
                )
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
                metadata={
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

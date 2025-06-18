from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import os

from src.database import get_db
from src.models.user import User  # Changed from src.models_backup.user
from src.middleware.auth_middleware import get_current_user


class ProjectController:
    """
    Controller class for handling project-related operations.
    """

    @staticmethod
    async def get_projects(
        skip: int = 0,
        limit: int = 100,
        status=None,
        project_type=None,
        client_id=None,
        search=None,
        db=None,
    ):
        """
        Get all projects from the database with optional filtering.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Filter by project status
            project_type: Filter by project type
            client_id: Filter by client ID
            search: Search in project name and description
            db: Database session

        Returns:
            List of marketing project objects
        """
        from sqlalchemy import or_
        from sqlalchemy.future import select
        from src.models.project import (
            Project,
        )  # Changed from src.models_backup.marketing_project

        # Build the query
        query = select(Project)  # Apply filters if provided
        if status:
            query = query.where(Project.status == status)

        if project_type:
            query = query.where(Project.project_type == project_type)

        if client_id:
            query = query.where(Project.client_id == client_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )

        # Add pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_project(project_id: int, db):
        """
        Get a project by its ID.

        Args:
            project_id: ID of the project to retrieve
            db: Database session

        Returns:
            Marketing project object or None if not found

        Raises:
            HTTPException: If project is not found
        """
        from sqlalchemy.future import select
        from fastapi import HTTPException, status
        from src.models.project import (
            Project,
        )  # Changed from src.models_backup.marketing_project

        query = select(Project).where(Project.id == project_id)
        result = await db.execute(query)
        project = result.scalars().first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )

        return project @ staticmethod

    async def create_project(project_data, db, owner_id=None):
        """
        Create a new project with the given data.

        Args:
            project_data: Project data from the request
            db: Database session

        Returns:
            Created marketing project object"""
        from src.models.project import (
            Project,
        )  # Changed from src.models_backup.marketing_project        # Handle both Pydantic models and regular dictionaries

        if hasattr(project_data, "model_dump"):
            # Pydantic model from API
            project_dict = project_data.model_dump(exclude={"team_members"})
        else:
            # Regular dictionary from web form
            project_dict = dict(project_data)
            # Remove team_members if present
            project_dict.pop("team_members", None)

        # Filter to only include valid Project model fields
        valid_fields = {
            "name",
            "description",
            "start_date",
            "end_date",
            "status",
            "progress",
            "budget",
        }
        filtered_dict = {k: v for k, v in project_dict.items() if k in valid_fields}

        # Convert empty strings to None for optional fields
        for field in ["start_date", "end_date", "budget"]:
            if field in filtered_dict and filtered_dict[field] == "":
                filtered_dict[field] = None

        # Convert date strings to datetime objects if needed
        if "start_date" in filtered_dict and filtered_dict["start_date"]:
            if isinstance(filtered_dict["start_date"], str):
                from datetime import datetime

                filtered_dict["start_date"] = datetime.fromisoformat(
                    filtered_dict["start_date"]
                )

        if "end_date" in filtered_dict and filtered_dict["end_date"]:
            if isinstance(filtered_dict["end_date"], str):
                from datetime import datetime

                filtered_dict["end_date"] = datetime.fromisoformat(
                    filtered_dict["end_date"]
                )  # Set owner_id if provided
        if owner_id:
            filtered_dict["owner_id"] = owner_id

        # Create new project
        project = Project(**filtered_dict)

        # Add to database
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # Handle team members if provided
        if hasattr(project_data, "team_members") and project_data.team_members:
            from src.models.association_tables import (
                project_team_association,
            )  # Changed path

            for team_member in project_data.team_members:
                await db.execute(
                    project_team_association.insert().values(
                        project_id=project.id,
                        user_id=team_member.user_id,
                        role=team_member.role,
                        joined_at=team_member.joined_at or datetime.utcnow(),
                    )
                )

            await db.commit()

        return project

    @staticmethod
    async def update_project(project_id: int, project_data, db):
        """
        Update a project with the given data.

        Args:
            project_id: ID of the project to update
            project_data: Updated project data
            db: Database session

        Returns:
            Updated marketing project object

        Raises:
            HTTPException: If project is not found
        """
        # First get the project
        project = await ProjectController.get_project(project_id, db)

        # Update attributes
        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        # Commit changes
        await db.commit()
        await db.refresh(project)

        return project

    @staticmethod
    async def delete_project(project_id: int, db):
        """
        Delete a project by ID.

        Args:
            project_id: ID of the project to delete
            db: Database session

        Returns:
            Boolean indicating success

        Raises:
            HTTPException: If project is not found
        """
        # First get the project
        project = await ProjectController.get_project(project_id, db)

        # Delete the project
        await db.delete(project)
        await db.commit()

        return True

    @staticmethod
    async def get_user_projects(user_id: int, db):
        """
        Get projects that a user has access to.

        Args:
            user_id: ID of the user
            db: Database session

        Returns:
            List of projects the user can access
        """
        from sqlalchemy.future import select
        from src.models.project import Project

        try:
            # For now, get all projects - in a real app you'd filter by user permissions
            query = select(Project).order_by(Project.name)
            result = await db.execute(query)
            projects = result.scalars().all()

            return projects
        except Exception as e:
            print(f"Error fetching user projects: {e}")
            return []


# Create the router
router = APIRouter(
    prefix="/project",
    tags=["project"],
    responses={404: {"description": "Not found"}},
)

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "../web/project/templates")
templates = Jinja2Templates(directory=templates_path)


# Define the routes
@router.get("/", response_class=HTMLResponse)
async def projects_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Render the projects list page with the modern template.
    """
    # In a real application, we would fetch projects from the database
    # For now, we'll just render the template
    return templates.TemplateResponse(
        "projects_modern.html", {"request": request, "current_user": current_user}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_project_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Render the new project form page with the modern template.
    """
    return templates.TemplateResponse(
        "new_project_modern.html", {"request": request, "current_user": current_user}
    )


@router.get("/{project_id}", response_class=HTMLResponse)
async def project_details_page(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Render the project details page with the modern template.
    """
    # In a real application, we would fetch the project from the database
    # For now, we'll just render the template
    return templates.TemplateResponse(
        "project_details_modern.html",
        {"request": request, "current_user": current_user, "project_id": project_id},
    )


@router.post("/create")
async def create_project(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form(...),
    priority: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    manager_id: int = Form(...),
    department: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Handle the creation of a new project from the form submission.
    """
    # In a real application, we would create a project in the database
    # For now, we'll just redirect to the projects page

    # Parse the form data
    project_data = {
        "name": name,
        "description": description,
        "status": status,
        "priority": priority,
        "start_date": start_date,
        "end_date": end_date,
        "manager_id": manager_id,
        "department": department,
        "tags": tags.split(",") if tags else [],
    }

    # Log the project creation (for demonstration purposes)
    print(f"Creating new project: {project_data}")

    # Return success response
    return {
        "success": True,
        "message": "Project created successfully",
        "redirect_url": "/project",
    }

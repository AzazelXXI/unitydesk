from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
    Request,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging

from src.database import get_db
from src.controllers.project_controller import ProjectController
from src.middleware.auth_middleware import (
    get_current_user,
    get_current_user_from_cookie,
)
from src.models.user import User

# Temporarily commenting out enum imports as we use Any placeholders
# from src.models.project import (
#     ProjectStatus,
#     ProjectType,
# )

# Using Any as placeholders for enums to allow the application to start
from typing import Any

ProjectStatus = Any
ProjectType = Any

from src.schemas.marketing_project import (
    MarketingProjectCreate,
    MarketingProjectUpdate,
    MarketingProjectRead,
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["marketing projects"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/", response_model=MarketingProjectRead, status_code=status.HTTP_201_CREATED
)
async def create_project(
    name: str = Form(...),
    description: str = Form(""),
    project_status: str = Form("PLANNING"),
    start_date: str = Form(None),
    target_end_date: str = Form(None),
    estimated_budget: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Create a new marketing project
    """
    logger.info(f"Creating project: {name}")
    logger.info(f"Current user: {current_user.id}")

    try:
        # Convert form data to proper types
        project_data = {
            "name": name,
            "description": description,
            "status": project_status,
            "start_date": start_date if start_date else None,
            "target_end_date": target_end_date if target_end_date else None,
            "estimated_budget": float(estimated_budget) if estimated_budget else None,
            "owner_id": current_user.id,  # Set current user as owner
        }

        logger.info(f"Project data: {project_data}")

        # Create MarketingProjectCreate object
        project_create = MarketingProjectCreate(**project_data)

        # Create project using controller
        project = await ProjectController.create_project(
            project_create, db, current_user.id
        )
        return project

    except Exception as e:
        logger.error(f"Error creating project: {str(e)}", exc_info=True)

        # Handle unique constraint violation for project name
        if "duplicate key value violates unique constraint" in str(
            e
        ) and "projects_name_key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A project with the name '{name}' already exists. Please choose a different name.",
            )

        # Handle other validation errors
        if "ValidationError" in str(type(e)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project data: {str(e)}",
            )

        # Handle all other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the project. Please try again.",
        )


@router.get("/", response_model=List[MarketingProjectRead])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProjectStatus] = None,
    client_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Get all marketing projects with optional filtering
    """
    return await ProjectController.get_projects(
        skip, limit, status, None, client_id, search, db
    )


@router.get("/{project_id}", response_model=MarketingProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific marketing project by ID
    """
    return await ProjectController.get_project(project_id, db)


@router.put("/{project_id}", response_model=MarketingProjectRead)
async def update_project(
    project_id: int,
    project_data: MarketingProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a marketing project
    """
    return await ProjectController.update_project(project_id, project_data, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a marketing project
    """
    await ProjectController.delete_project(project_id, db)

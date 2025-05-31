from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from src.database import get_db
from src.controllers.project_controller import ProjectController
from src.models_backup.marketing_project import ProjectStatus, ProjectType
from src.schemas.marketing_project import (
    MarketingProjectCreate, MarketingProjectUpdate, MarketingProjectRead
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["marketing projects"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=MarketingProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: MarketingProjectCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new marketing project
    """
    return await ProjectController.create_project(project_data, db)


@router.get("/", response_model=List[MarketingProjectRead])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProjectStatus] = None,
    project_type: Optional[ProjectType] = None,
    client_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all marketing projects with optional filtering
    """
    return await ProjectController.get_projects(skip, limit, status, project_type, client_id, search, db)


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
    db: AsyncSession = Depends(get_db)
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

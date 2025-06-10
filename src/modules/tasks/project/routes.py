# API Endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.controllers.project_controller import ProjectController
from .schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from .dependencies import get_current_user, require_project_manager
from .service import ProjectService

router = APIRouter(prefix="/api/v2/projects", tags=["projects-v2"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager),
):
    """Create a new project - Only Project Managers can create projects"""
    return await ProjectService.create_project(project_data, current_user.id, db)


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of projects with optional filtering"""
    return await ProjectService.get_projects(current_user.id, skip, limit, status, db)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get project details by ID"""
    return await ProjectService.get_project_by_id(project_id, current_user.id, db)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager),
):
    """Update project - Only Project Managers can update"""
    return await ProjectService.update_project(
        project_id, project_data, current_user.id, db
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager),
):
    """Delete project - Only Project Managers can delete"""
    await ProjectService.delete_project(project_id, current_user.id, db)


@router.get("/{project_id}/team", response_model=List[dict])
async def get_project_team(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get project team members"""
    return await ProjectService.get_project_team(project_id, current_user.id, db)


@router.post("/{project_id}/team/{user_id}")
async def add_team_member(
    project_id: str,
    user_id: str,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_project_manager),
):
    """Add team member to project"""
    return await ProjectService.add_team_member(
        project_id, user_id, role, current_user.id, db
    )

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from src.database import get_db
from src.controllers.asset_controller import AssetController
from src.models_backup.marketing_project import AssetType
from src.schemas.marketing_project import (
    MarketingAssetCreate, MarketingAssetUpdate, MarketingAssetRead
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["marketing assets"],
    responses={404: {"description": "Not found"}}
)


@router.post("/{project_id}/assets", response_model=MarketingAssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset(
    project_id: int,
    asset_data: MarketingAssetCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new marketing asset for a project
    """
    return await AssetController.create_asset(project_id, asset_data, db)


@router.post("/{project_id}/assets/upload", response_model=MarketingAssetRead, status_code=status.HTTP_201_CREATED)
async def upload_asset_file(
    project_id: int,
    file: UploadFile = File(...),
    name: str = Query(..., description="Asset name"),
    description: Optional[str] = Query(None, description="Asset description"),
    asset_type: AssetType = Query(..., description="Asset type"),
    related_task_id: Optional[int] = Query(None, description="Related task ID"),
    creator_id: int = Query(..., description="Creator user ID"),
    is_final: bool = Query(False, description="Whether this is a final version"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file as a marketing asset for a project
    """
    return await AssetController.upload_asset_file(
        project_id, file, name, description, asset_type,
        related_task_id, creator_id, is_final, db
    )


@router.get("/{project_id}/assets", response_model=List[MarketingAssetRead])
async def get_project_assets(
    project_id: int,
    asset_type: Optional[AssetType] = None,
    is_final: Optional[bool] = None,
    related_task_id: Optional[int] = None,
    shared_with_client: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all marketing assets for a project with optional filtering
    """
    return await AssetController.get_project_assets(
        project_id, asset_type, is_final, related_task_id,
        shared_with_client, search, db
    )


@router.get("/{project_id}/assets/{asset_id}", response_model=MarketingAssetRead)
async def get_asset(
    project_id: int,
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific marketing asset
    """
    return await AssetController.get_asset(project_id, asset_id, db)


@router.put("/{project_id}/assets/{asset_id}", response_model=MarketingAssetRead)
async def update_asset(
    project_id: int,
    asset_id: int,
    asset_data: MarketingAssetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a marketing asset
    """
    return await AssetController.update_asset(project_id, asset_id, asset_data, db)


@router.delete("/{project_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    project_id: int,
    asset_id: int,
    delete_file: bool = Query(False, description="Whether to delete the physical file"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a marketing asset
    """
    await AssetController.delete_asset(project_id, asset_id, delete_file, db)


@router.put("/{project_id}/assets/{asset_id}/share", response_model=MarketingAssetRead)
async def toggle_client_sharing(
    project_id: int,
    asset_id: int,
    shared: bool = Query(..., description="Whether to share with the client"),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle sharing of an asset with the client
    """
    return await AssetController.toggle_client_sharing(project_id, asset_id, shared, db)


@router.post("/{project_id}/assets/{asset_id}/client-feedback", response_model=MarketingAssetRead)
async def add_client_feedback(
    project_id: int,
    asset_id: int,
    feedback: str = Query(..., description="Client feedback"),
    db: AsyncSession = Depends(get_db)
):
    """
    Add client feedback to a marketing asset
    """
    return await AssetController.add_client_feedback(project_id, asset_id, feedback, db)

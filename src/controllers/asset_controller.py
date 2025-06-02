from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import os
import shutil
from uuid import uuid4
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import and_

from src.database import get_db

# from src.models.project import MarketingProject, MarketingAsset, AssetType # Changed path
# from src.models.task import MarketingTask # Changed path
# from src.schemas.marketing_project import (
#     MarketingAssetCreate, MarketingAssetUpdate, MarketingAssetRead
# )

# Configure logging
logger = logging.getLogger(__name__)


class AssetController:
    """Controller for handling marketing asset operations"""

    pass  # Comment out all methods as they depend on the missing models


#     @staticmethod
#     async def create_asset(
#         project_id: int,
#         asset_data: MarketingAssetCreate,
#         db: AsyncSession
#     ) -> MarketingAsset:
#         """
#         Create a new marketing asset for a project
#         """
#         try:
#             # Verify project exists
#             project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
#             project_result = await db.execute(project_query)
#             project = project_result.scalars().first()

#             if not project:
#                 logger.warning(f"Project with ID {project_id} not found")
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Project with ID {project_id} not found"
#                 )

#             # If related to a task, verify task exists and belongs to the project
#             if asset_data.related_task_id:
#                 task_query = select(MarketingTask).filter(
#                     MarketingTask.id == asset_data.related_task_id,
#                     MarketingTask.project_id == project_id
#                 )
#                 task_result = await db.execute(task_query)
#                 task = task_result.scalars().first()

#                 if not task:
#                     logger.warning(f"Task with ID {asset_data.related_task_id} not found for project {project_id}")
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Task with ID {asset_data.related_task_id} not found for project {project_id}"
#                     )

#             # Create the asset
#             new_asset = MarketingAsset(
#                 project_id=project_id,
#                 related_task_id=asset_data.related_task_id,
#                 name=asset_data.name,
#                 description=asset_data.description,
#                 asset_type=asset_data.asset_type,
#                 file_path=asset_data.file_path,
#                 file_url=asset_data.file_url,
#                 file_size=asset_data.file_size,
#                 mime_type=asset_data.mime_type,
#                 version=asset_data.version,
#                 is_final=asset_data.is_final,
#                 creator_id=asset_data.creator_id,
#                 approved_by_id=asset_data.approved_by_id,
#                 approved_at=asset_data.approved_at,
#                 shared_with_client=asset_data.shared_with_client,
#                 client_feedback=asset_data.client_feedback
#             )

#             db.add(new_asset)
#             await db.commit()
#             await db.refresh(new_asset)

#             logger.info(f"Created new marketing asset: {new_asset.name} for project {project_id}")

#             # Return the created asset with related info
#             asset_query = select(MarketingAsset).filter(
#                 MarketingAsset.id == new_asset.id
#             ).options(
#                 joinedload(MarketingAsset.creator),
#                 joinedload(MarketingAsset.approved_by),
#                 joinedload(MarketingAsset.project),
#                 joinedload(MarketingAsset.related_task)
#             )

#             result = await db.execute(asset_query)
#             asset = result.scalars().first()

#             return asset
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Error creating marketing asset for project {project_id}: {str(e)}")
#             await db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to create marketing asset: {str(e)}"
#             )

#     @staticmethod
#     async def upload_asset_file(
#         project_id: int,
#         file: UploadFile,
#         name: str,
#         description: Optional[str],
#         asset_type: AssetType,
#         related_task_id: Optional[int],
#         creator_id: int,
#         is_final: bool,
#         db: AsyncSession
#     ) -> MarketingAsset:
#         """
#         Upload a file as a marketing asset for a project
#         """
#         try:
#             # Verify project exists
#             project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
#             project_result = await db.execute(project_query)
#             project = project_result.scalars().first()

#             if not project:
#                 logger.warning(f"Project with ID {project_id} not found")
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Project with ID {project_id} not found"
#                 )

#             # If related to a task, verify task exists and belongs to the project
#             if related_task_id:
#                 task_query = select(MarketingTask).filter(
#                     MarketingTask.id == related_task_id,
#                     MarketingTask.project_id == project_id
#                 )
#                 task_result = await db.execute(task_query)
#                 task = task_result.scalars().first()

#                 if not task:
#                     logger.warning(f"Task with ID {related_task_id} not found for project {project_id}")
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Task with ID {related_task_id} not found for project {project_id}"
#                     )

#             # Create directory for project assets if it doesn\'t exist
#             upload_dir = f"uploads/projects/{project_id}/assets"
#             os.makedirs(upload_dir, exist_ok=True)

#             # Generate unique filename
#             file_extension = os.path.splitext(file.filename)[1]
#             unique_filename = f"{uuid4()}{file_extension}"
#             file_path = f"{upload_dir}/{unique_filename}"

#             # Save file
#             with open(file_path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)

#             # Get file size
#             file_size = os.path.getsize(file_path)

#             # Create asset in database
#             new_asset = MarketingAsset(
#                 project_id=project_id,
#                 related_task_id=related_task_id,
#                 name=name,
#                 description=description,
#                 asset_type=asset_type,
#                 file_path=file_path,
#                 file_url=f"/api/assets/{unique_filename}",  # URL for accessing the file
#                 file_size=file_size,
#                 mime_type=file.content_type,
#                 version="1.0",  # Initial version
#                 is_final=is_final,
#                 creator_id=creator_id,
#                 shared_with_client=False
#             )

#             db.add(new_asset)
#             await db.commit()
#             await db.refresh(new_asset)

#             logger.info(f"Uploaded new marketing asset: {new_asset.name} for project {project_id}")

#             # Return the created asset with related info
#             asset_query = select(MarketingAsset).filter(
#                 MarketingAsset.id == new_asset.id
#             ).options(
#                 joinedload(MarketingAsset.creator),
#                 joinedload(MarketingAsset.project),
#                 joinedload(MarketingAsset.related_task)
#             )

#             result = await db.execute(asset_query)
#             asset = result.scalars().first()

#             return asset
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Error uploading marketing asset for project {project_id}: {str(e)}")
#             await db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to upload marketing asset: {str(e)}"
#             )

#     @staticmethod
#     async def get_project_assets(
#         project_id: int,
#         asset_type: Optional[AssetType],
#         is_final: Optional[bool],
#         related_task_id: Optional[int],
#         shared_with_client: Optional[bool],
#         search: Optional[str],
#         db: AsyncSession
#     ) -> List[MarketingAsset]:
#         """
#         Get all marketing assets for a project with optional filtering
#         """
#         try:
#             # Verify project exists
#             project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
#             project_result = await db.execute(project_query)
#             project = project_result.scalars().first()

#             if not project:
#                 logger.warning(f"Project with ID {project_id} not found")
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Project with ID {project_id} not found"
#                 )

#             # Build query with filters
#             query = select(MarketingAsset).filter(MarketingAsset.project_id == project_id)

#             if asset_type:
#                 query = query.filter(MarketingAsset.asset_type == asset_type)
#             if is_final is not None:
#                 query = query.filter(MarketingAsset.is_final == is_final)
#             if related_task_id:
#                 query = query.filter(MarketingAsset.related_task_id == related_task_id)
#             if shared_with_client is not None:
#                 query = query.filter(MarketingAsset.shared_with_client == shared_with_client)
#             if search:
#                 query = query.filter(MarketingAsset.name.ilike(f"%{search}%"))

#             # Add eager loading
#             query = query.options(
#                 joinedload(MarketingAsset.creator),
#                 joinedload(MarketingAsset.approved_by),
#                 joinedload(MarketingAsset.project),
#                 joinedload(MarketingAsset.related_task)
#             )

#             # Execute query
#             result = await db.execute(query)
#             assets = result.scalars().all()

#             return assets
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Error fetching marketing assets for project {project_id}: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to fetch marketing assets: {str(e)}"
#             )

#     @staticmethod
#     async def get_asset(
#         project_id: int,
#         asset_id: int,
#         db: AsyncSession
#     ) -> MarketingAsset:
#         """
#         Get a specific marketing asset
#         """
#         try:
#             # Query with eager loading
#             query = select(MarketingAsset).filter(
#                 MarketingAsset.project_id == project_id,
#                 MarketingAsset.id == asset_id
#             ).options(
#                 joinedload(MarketingAsset.creator),
#                 joinedload(MarketingAsset.approved_by),
#                 joinedload(MarketingAsset.project),
#                 joinedload(MarketingAsset.related_task)
#             )

#             result = await db.execute(query)
#             asset = result.scalars().first()

#             if not asset:
#                 logger.warning(f"Asset with ID {asset_id} not found for project {project_id}")
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Asset with ID {asset_id} not found for project {project_id}"
#                 )

#             return asset
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Error fetching marketing asset {asset_id}: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to fetch marketing asset: {str(e)}"
#             )

#     @staticmethod
#     async def update_asset(
#         project_id: int,
#         asset_id: int,
#         asset_data: MarketingAssetUpdate,
#         db: AsyncSession
#     ) -> MarketingAsset:
#         """
#         Update a marketing asset
#         """
#         try:
#             # Get the asset
#             query = select(MarketingAsset).filter(
#                 MarketingAsset.project_id == project_id,
#                 MarketingAsset.id == asset_id
#             )

#             result = await db.execute(query)
#             asset = result.scalars().first()

#             if not asset:
#                 logger.warning(f"Asset with ID {asset_id} not found for project {project_id}")
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Asset with ID {asset_id} not found for project {project_id}"
#                 )

#             # Update asset attributes
#             update_data = asset_data.dict(exclude_unset=True)

#             # Handle approval logic
#             if asset_data.approved_by_id and not asset.approved_at:
#                 update_data["approved_at"] = datetime.utcnow()

#             for key, value in update_data.items():
#                 if value is not None:
#                     setattr(asset, key, value)

#             await db.commit()
#             await db.refresh(asset)

#             logger.info(f"Updated marketing asset {asset_id} for project {project_id}")

#             # Return the updated asset with full details
#             return await AssetController.get_asset(project_id, asset_id, db)
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Error updating marketing asset {asset_id}: {str(e)}")
#             await db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to update marketing asset: {str(e)}"
#             )

#     @staticmethod
#     async def delete_asset(
#         project_id: int,
#         asset_id: int,
#         delete_file: bool,
#         db: AsyncSession
#     ) -> None:
#         """
#         Delete a marketing asset
#         """
#         try:
#             # Get the asset
#             query = select(MarketingAsset).filter(
#                 MarketingAsset.project_id == project_id,
#                 MarketingAsset.id == asset_id
#             )

#             result = await db.execute(query)
#             asset = result.scalars().first()

#             if not asset:
#                 logger.warning(f"Asset with ID {asset_id} not found for project {project_id}")
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Asset with ID {asset_id} not found for project {project_id}"
#                 )

#             # Delete file from storage if requested
#             if delete_file and asset.file_path and os.path.exists(asset.file_path):
#                 try:
#                     os.remove(asset.file_path)
#                     logger.info(f"Deleted asset file: {asset.file_path}")
#                 except OSError as e:
#                     logger.error(f"Error deleting asset file {asset.file_path}: {str(e)}")
#                     # Optionally, decide if this should prevent asset deletion from DB

#             await db.delete(asset)
#             await db.commit()

#             logger.info(f"Deleted marketing asset {asset_id} from project {project_id}")
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Error deleting marketing asset {asset_id}: {str(e)}")
#             await db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to delete marketing asset: {str(e)}"
#             )

# # Example of how to get a file (e.g., for download)
# # This would typically be in a route handler
# # from fastapi import File, Response
# # from fastapi.responses import FileResponse

# # @router.get(\"/assets/{filename}\") # Assuming 'router' is your FastAPI APIRouter
# # async def get_asset_file(filename: str, project_id: int, db: AsyncSession = Depends(get_db)):
# #     # Basic security: ensure filename is safe, and user has access
# #     # This is a simplified example. You'd need robust access control.

# #     # Find asset by filename and project_id to get the actual file_path
# #     # This requires storing filename or a unique ID that maps to the file_path
# #     # For simplicity, let's assume filename is unique enough for this example

# #     # Construct the full path. IMPORTANT: Sanitize `filename` to prevent directory traversal.
# #     # A better approach is to store a mapping of a safe ID to the actual file path.
# #     base_upload_dir = f\"uploads/projects/{project_id}/assets\"
# #     file_path = os.path.join(base_upload_dir, filename) # os.path.join helps with path safety

# #     if not os.path.exists(file_path) or not os.path.isfile(file_path):
# #         raise HTTPException(status_code=404, detail=\"File not found\")

# #     # To get MIME type, you might store it with the asset or infer it
# #     # For this example, we'll try to infer, but storing it is more reliable.
# #     # mime_type, _ = mimetypes.guess_type(file_path)
# #     # if mime_type is None:
# #     #     mime_type = \"application/octet-stream\" # Default if cannot infer

# #     # Find the asset in DB to get its stored mime_type
# #     asset_query = select(MarketingAsset).filter(
# #         MarketingAsset.project_id == project_id,
# #         MarketingAsset.file_path == file_path # Or using a unique file ID
# #     )
# #     result = await db.execute(asset_query)
# #     asset = result.scalars().first()

# #     if not asset:
# #         raise HTTPException(status_code=404, detail=\"Asset record not found for this file\")

# #     return FileResponse(path=file_path, filename=asset.name, media_type=asset.mime_type)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime
from fastapi import HTTPException, UploadFile
import os
import io

from src.controllers.asset_controller import AssetController
from src.models_backup.marketing_project import (
    MarketingProject, MarketingTask, MarketingAsset, AssetType
)

# Mock fixtures
@pytest.fixture
def mock_db():
    """Create a mock async database session"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.add = AsyncMock()
    db.delete = AsyncMock()
    
    # Mock execute() to allow chaining
    result_mock = AsyncMock()
    db.execute.return_value = result_mock
    
    # Mock scalar methods
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    result_mock.scalars = MagicMock()
    result_mock.scalars.return_value.first = MagicMock(return_value=None)
    result_mock.scalars.return_value.all = MagicMock(return_value=[])
    
    return db

@pytest.fixture
def mock_project():
    """Create a mock MarketingProject"""
    project = MagicMock(spec=MarketingProject)
    project.id = 1
    project.name = "Test Project"
    project.description = "Test project description"
    project.client_id = 1
    project.status = "ACTIVE"
    project.current_stage = "PLANNING"
    project.start_date = datetime.now()
    project.target_end_date = datetime.now()
    return project

@pytest.fixture
def mock_task():
    """Create a mock MarketingTask"""
    task = MagicMock(spec=MarketingTask)
    task.id = 1
    task.project_id = 1
    task.title = "Test Task"
    task.description = "Test task description"
    task.status = "IN_PROGRESS"
    task.priority = "MEDIUM"
    task.created_at = datetime.now()
    task.updated_at = datetime.now()
    return task

@pytest.fixture
def mock_asset():
    """Create a mock MarketingAsset"""
    asset = MagicMock(spec=MarketingAsset)
    asset.id = 1
    asset.project_id = 1
    asset.related_task_id = 1
    asset.name = "Test Asset"
    asset.description = "Test asset description"
    asset.asset_type = AssetType.IMAGE
    asset.file_path = "uploads/projects/1/assets/test_asset.jpg"
    asset.file_url = "/api/assets/test_asset.jpg"
    asset.file_size = 1024
    asset.mime_type = "image/jpeg"
    asset.version = "1.0"
    asset.is_final = False
    asset.creator_id = 1
    asset.created_at = datetime.now()
    asset.updated_at = datetime.now()
    asset.approved_by_id = None
    asset.approved_at = None
    asset.shared_with_client = False
    asset.client_feedback = None
    asset.creator = MagicMock()
    asset.approved_by = None
    return asset

@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile"""
    content = io.BytesIO(b"file content")
    upload_file = MagicMock(spec=UploadFile)
    upload_file.filename = "test_image.jpg"
    upload_file.content_type = "image/jpeg"
    upload_file.file = content
    return upload_file


class TestAssetController:
    """Tests for AssetController class"""
    
    @pytest.mark.asyncio
    async def test_create_asset(self, mock_db, mock_project, mock_asset):
        """Test creating a new marketing asset"""
        # Arrange
        asset_data = MagicMock()
        asset_data.related_task_id = None
        asset_data.name = "Test Asset"
        asset_data.description = "Test asset description"
        asset_data.asset_type = AssetType.IMAGE
        asset_data.file_path = "uploads/projects/1/assets/test_asset.jpg"
        asset_data.file_url = "/api/assets/test_asset.jpg"
        asset_data.file_size = 1024
        asset_data.mime_type = "image/jpeg"
        asset_data.version = "1.0"
        asset_data.is_final = False
        asset_data.creator_id = 1
        asset_data.approved_by_id = None
        asset_data.approved_at = None
        asset_data.shared_with_client = False
        asset_data.client_feedback = None
        
        # Set up the mock database to return the project and asset
        mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_project, mock_asset]
        
        # Act
        result = await AssetController.create_asset(1, asset_data, mock_db)
        
        # Assert
        assert result == mock_asset
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_asset_project_not_found(self, mock_db):
        """Test creating an asset for a non-existent project"""
        # Arrange
        asset_data = MagicMock()
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await AssetController.create_asset(999, asset_data, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_upload_asset_file(self, mock_db, mock_project, mock_asset, mock_upload_file):
        """Test uploading a file as an asset"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_project, mock_asset]
        
        # Mock os.makedirs, open, and os.path.getsize
        with patch('os.makedirs'), patch('builtins.open', mock_open()), patch('os.path.getsize', return_value=1024), \
             patch('uuid.uuid4', return_value="test-uuid"):
            # Act
            result = await AssetController.upload_asset_file(
                1, mock_upload_file, "Test Asset", "Test description", AssetType.IMAGE, 
                None, 1, False, mock_db
            )
            
            # Assert
            assert result == mock_asset
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_project_assets(self, mock_db, mock_project, mock_asset):
        """Test getting assets for a project"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_project
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_asset]
        
        # Act
        result = await AssetController.get_project_assets(
            1, None, None, None, None, False, mock_db
        )
        
        # Assert
        assert len(result) == 1
        assert result[0] == mock_asset
    
    @pytest.mark.asyncio
    async def test_get_asset(self, mock_db, mock_asset):
        """Test getting a specific asset"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_asset
        
        # Act
        result = await AssetController.get_asset(1, 1, mock_db)
        
        # Assert
        assert result == mock_asset
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_asset_not_found(self, mock_db):
        """Test getting a non-existent asset"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await AssetController.get_asset(1, 999, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_asset(self, mock_db, mock_asset):
        """Test updating an asset"""
        # Arrange
        asset_data = MagicMock()
        asset_data.dict.return_value = {
            "name": "Updated Asset Name",
            "description": "Updated description",
            "is_final": True
        }
        
        mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_asset, mock_asset]
        
        # Act
        result = await AssetController.update_asset(1, 1, asset_data, mock_db)
        
        # Assert
        assert result == mock_asset
        assert mock_asset.name == "Updated Asset Name"
        assert mock_asset.description == "Updated description"
        assert mock_asset.is_final == True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_asset(self, mock_db, mock_asset):
        """Test deleting an asset"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_asset
        
        # Mock os.path.exists and os.remove
        with patch('os.path.exists', return_value=True), patch('os.remove'):
            # Act
            await AssetController.delete_asset(1, 1, True, mock_db)
            
            # Assert
            mock_db.delete.assert_called_once_with(mock_asset)
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_asset_with_client(self, mock_db, mock_asset):
        """Test sharing an asset with a client"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_asset
        
        # Act
        result = await AssetController.share_asset_with_client(1, 1, True, mock_db)
    
        # Assert
        assert result == mock_asset
        assert mock_asset.shared_with_client == True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_client_feedback(self, mock_db, mock_asset):
        """Test adding client feedback to an asset"""
        # Arrange
        feedback = "This looks great!"
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_asset
        
        # Act
        result = await AssetController.add_client_feedback(1, 1, feedback, mock_db)
        
        # Assert
        assert result == mock_asset
        assert mock_asset.client_feedback == feedback
        mock_db.commit.assert_called_once()

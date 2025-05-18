import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException
import os
import json

from src.controllers.analytics_controller import AnalyticsController
from src.models.marketing_project import MarketingProject, AnalyticsReport, ReportType

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
    project.start_date = datetime.now() - timedelta(days=30)
    project.target_end_date = datetime.now() + timedelta(days=30)
    return project

@pytest.fixture
def mock_report():
    """Create a mock AnalyticsReport"""
    report = MagicMock(spec=AnalyticsReport)
    report.id = 1
    report.project_id = 1
    report.report_type = ReportType.PERFORMANCE
    report.title = "Test Report"
    report.description = "Test report description"
    report.content = "Test content"
    report.insights = "Test insights"
    report.recommendations = "Test recommendations"
    report.period_start = datetime.now() - timedelta(days=30)
    report.period_end = datetime.now()
    report.is_draft = True
    report.creator_id = 1
    report.approved_by_id = None
    report.created_at = datetime.now()
    report.updated_at = datetime.now()
    report.file_path = "uploads/projects/1/reports/test_report.pdf"
    report.file_url = "/api/reports/test_report.pdf"
    report.metrics = json.dumps({"views": 1000, "clicks": 200})
    return report


class TestAnalyticsController:
    """Tests for AnalyticsController class"""
    
    @pytest.mark.asyncio
    async def test_create_report(self, mock_db, mock_project, mock_report):
        """Test creating a new analytics report"""
        # Arrange
        report_data = MagicMock()
        report_data.report_type = ReportType.PERFORMANCE
        report_data.title = "Test Report"
        report_data.description = "Test report description"
        report_data.content = "Test content"
        report_data.insights = "Test insights"
        report_data.recommendations = "Test recommendations"
        report_data.period_start = datetime.now() - timedelta(days=30)
        report_data.period_end = datetime.now()
        report_data.is_draft = True
        report_data.creator_id = 1
        report_data.approved_by_id = None
        report_data.file_path = None
        report_data.file_url = None
        report_data.metrics = json.dumps({"views": 1000, "clicks": 200})
        
        # Set up the mock database to return the project and report
        mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_project, mock_report]
        
        # Act
        result = await AnalyticsController.create_report(1, report_data, mock_db)
        
        # Assert
        assert result == mock_report
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_report_project_not_found(self, mock_db):
        """Test creating a report for a non-existent project"""
        # Arrange
        report_data = MagicMock()
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await AnalyticsController.create_report(999, report_data, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_project_reports(self, mock_db, mock_project, mock_report):
        """Test getting reports for a project"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_project
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_report]
        
        # Act
        result = await AnalyticsController.get_project_reports(
            1, None, None, None, None, None, None, mock_db
        )
        
        # Assert
        assert len(result) == 1
        assert result[0] == mock_report
        mock_db.execute.call_count == 2  # First call checks project, second gets reports
    
    @pytest.mark.asyncio
    async def test_get_report(self, mock_db, mock_report):
        """Test getting a specific report"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_report
        
        # Act
        result = await AnalyticsController.get_report(1, 1, mock_db)
        
        # Assert
        assert result == mock_report
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_report_not_found(self, mock_db):
        """Test getting a non-existent report"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await AnalyticsController.get_report(1, 999, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_report(self, mock_db, mock_report):
        """Test updating a report"""
        # Arrange
        report_data = MagicMock()
        report_data.dict.return_value = {
            "title": "Updated Title",
            "insights": "Updated insights"
        }
        
        mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_report, mock_report]
        
        # Act
        result = await AnalyticsController.update_report(1, 1, report_data, mock_db)
        
        # Assert
        assert result == mock_report
        assert mock_report.title == "Updated Title"
        assert mock_report.insights == "Updated insights"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_report(self, mock_db, mock_report):
        """Test deleting a report"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_report
        
        # Mock os.path.exists and os.remove
        with patch('os.path.exists', return_value=True), patch('os.remove'):
            # Act
            await AnalyticsController.delete_report(1, 1, True, mock_db)
            
            # Assert
            mock_db.delete.assert_called_once_with(mock_report)
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_report(self, mock_db, mock_report):
        """Test publishing a draft report"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.side_effect = [mock_report, mock_report]
        
        # Act
        result = await AnalyticsController.publish_report(1, 1, 2, mock_db)
        
        # Assert
        assert result == mock_report
        assert mock_report.is_draft == False
        assert mock_report.approved_by_id == 2
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_project_dashboard(self, mock_db, mock_project, mock_report):
        """Test getting project dashboard data"""
        # Arrange
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_project
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_report]
        
        # Act
        result = await AnalyticsController.get_project_dashboard(1, 30, mock_db)
        
        # Assert
        assert "project_info" in result
        assert "latest_reports" in result
        assert "metrics_collection" in result
        assert "period" in result
        assert result["project_info"]["id"] == mock_project.id
        assert len(result["latest_reports"]) == 1
        assert len(result["metrics_collection"]) == 1

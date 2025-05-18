import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json

from src.controllers.meeting_controller import MeetingController
from src.schemas.meeting import MeetingCreate, MeetingUpdate

class TestMeetingController:
    """Tests for the meeting controller"""
    
    def setup_method(self):
        """Setup before each test"""
        self.controller = MeetingController()
    
    def test_get_meetings(self):
        """Test getting all meetings"""
        # Act
        meetings = self.controller.get_meetings()
        
        # Assert
        assert isinstance(meetings, list)
        assert len(meetings) == 2
        assert meetings[0]["id"] == 1
        assert meetings[0]["title"] == "Weekly Standup"
        assert meetings[0]["status"] == "scheduled"
        assert meetings[1]["id"] == 2
        assert meetings[1]["title"] == "Project Review"
        assert meetings[1]["status"] == "completed"
    
    def test_create_meeting(self):
        """Test creating a new meeting"""
        # Arrange
        # Mock the MeetingCreate schema
        meeting_data = MagicMock(spec=MeetingCreate)
        meeting_data.dict.return_value = {
            "title": "New Project Kickoff",
            "description": "Initial project meeting",
            "start_time": "2023-08-15T10:00:00",
            "end_time": "2023-08-15T11:00:00",
            "location": "Conference Room A",
            "status": "scheduled",
            "organizer_id": 1,
        }
        
        # Act
        result = self.controller.create_meeting(meeting_data)
        
        # Assert
        assert result["id"] == 3
        assert result["title"] == "New Project Kickoff"
        assert result["status"] == "scheduled"
        assert "created_at" in result
    
    def test_get_meeting_found(self):
        """Test getting a meeting that exists"""
        # Act
        meeting = self.controller.get_meeting(1)
        
        # Assert
        assert meeting is not None
        assert meeting["id"] == 1
        assert meeting["title"] == "Sample Meeting"
        assert meeting["status"] == "scheduled"
    
    def test_get_meeting_not_found(self):
        """Test getting a meeting that doesn't exist"""
        # Act
        meeting = self.controller.get_meeting(999)
        
        # Assert
        assert meeting is None
    
    def test_update_meeting_found(self):
        """Test updating a meeting that exists"""
        # Arrange
        meeting_data = MagicMock(spec=MeetingUpdate)
        meeting_data.dict.return_value = {
            "title": "Updated Meeting Title",
            "status": "in_progress"
        }
        
        # Act
        result = self.controller.update_meeting(1, meeting_data)
        
        # Assert
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "Updated Meeting Title"
        assert result["status"] == "in_progress"
        assert "updated_at" in result
    
    def test_update_meeting_not_found(self):
        """Test updating a meeting that doesn't exist"""
        # Arrange
        meeting_data = MagicMock(spec=MeetingUpdate)
        
        # Act
        result = self.controller.update_meeting(999, meeting_data)
        
        # Assert
        assert result is None
    
    def test_delete_meeting_found(self):
        """Test deleting a meeting that exists"""
        # Act
        result = self.controller.delete_meeting(1)
        
        # Assert
        assert result is True
    
    def test_delete_meeting_not_found(self):
        """Test deleting a meeting that doesn't exist"""
        # Act
        result = self.controller.delete_meeting(999)
        
        # Assert
        assert result is False

class TestMeetingControllerEdgeCases:
    """Tests for edge cases in the meeting controller"""
    
    def setup_method(self):
        """Setup before each test"""
        self.controller = MeetingController()
    
    def test_create_meeting_with_minimum_fields(self):
        """Test creating a meeting with only required fields"""
        # Arrange
        meeting_data = MagicMock(spec=MeetingCreate)
        meeting_data.dict.return_value = {
            "title": "Minimal Meeting",
            "start_time": "2023-08-15T10:00:00",
            "end_time": "2023-08-15T11:00:00",
        }
        
        # Act
        result = self.controller.create_meeting(meeting_data)
        
        # Assert
        assert result["id"] == 3
        assert result["title"] == "Minimal Meeting"
        assert "created_at" in result
    
    def test_update_meeting_partial_update(self):
        """Test updating only specific fields of a meeting"""
        # Arrange
        meeting_data = MagicMock(spec=MeetingUpdate)
        # exclude_unset=True makes it only update specified fields
        meeting_data.dict.return_value = {"status": "cancelled"}
        
        # Act
        result = self.controller.update_meeting(1, meeting_data)
        
        # Assert
        assert result is not None
        assert result["id"] == 1
        assert result["status"] == "cancelled"
        assert "updated_at" in result

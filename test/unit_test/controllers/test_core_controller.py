import pytest
from src.controllers.core_controller import CoreController


class TestCoreController:
    """Tests for CoreController class"""
    
    def setup_method(self):
        """Set up the test fixture before each test method is executed"""
        self.controller = CoreController()
    
    def test_get_core_info(self):
        """Test the get_core_info method returns correct information"""
        # Act
        result = self.controller.get_core_info()
        
        # Assert
        assert isinstance(result, dict)
        assert "name" in result
        assert "description" in result
        assert result["name"] == "CSA Platform API"
        assert result["description"] == "API for the Collaboration and Service Automation Platform"
    
    def test_health_check(self):
        """Test the health_check method returns healthy status"""
        # Act
        result = self.controller.health_check()
        
        # Assert
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "healthy"
    
    def test_get_version(self):
        """Test the get_version method returns correct version information"""
        # Act
        result = self.controller.get_version()
        
        # Assert
        assert isinstance(result, dict)
        assert "version" in result
        assert "api_version" in result
        assert result["version"] == "1.0.0"
        assert result["api_version"] == "v1"


if __name__ == "__main__":
    pytest.main()
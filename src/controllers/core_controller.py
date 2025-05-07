class CoreController:
    """Core controller for base API functionality"""
    
    def get_core_info(self):
        """Get basic information about the core API"""
        return {
            "name": "CSA Platform API",
            "description": "API for the Collaboration and Service Automation Platform"
        }
    
    def health_check(self):
        """Health check endpoint for monitoring"""
        return {"status": "healthy"}
    
    def get_version(self):
        """Get current API version information"""
        return {
            "version": "1.0.0",
            "api_version": "v1"
        }

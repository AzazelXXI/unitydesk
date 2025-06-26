#!/usr/bin/env python3
"""
Test if the application starts without the SQLAlchemy metadata error
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("Testing import of activity model...")
    from src.models.activity import ProjectActivity, ActivityType
    print("✅ Successfully imported activity model")
    
    print("Testing import of activity service...")
    from src.services.activity_service import ActivityService
    print("✅ Successfully imported activity service")
    
    print("Testing import of project routes...")
    from src.views.project.project_routes import router
    print("✅ Successfully imported project routes")
    
    print("Testing import of main application...")
    from src.main import app
    print("✅ Successfully imported main application")
    
    print("\n" + "=" * 50)
    print("🎉 ALL IMPORTS SUCCESSFUL!")
    print("The SQLAlchemy metadata error has been fixed!")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Import error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

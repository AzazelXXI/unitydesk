#!/usr/bin/env python3
"""
Create a new task and verify the activity is logged
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.services.activity_service import ActivityService
from src.models.activity import ActivityType

async def test_new_task_activity():
    # Load environment variables
    load_dotenv()
    
    # Database connection
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'azazeladmin')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'testdb')}"
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("🔍 Testing new task activity creation...")
            
            project_id = 18
            user_id = 1  # John Manager
            task_name = f"UI Test Task {datetime.now().strftime('%H:%M:%S')}"
            
            # Log a new task activity
            description = f'John Manager created task "{task_name}"'
            
            activity = await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=user_id,
                activity_type=ActivityType.TASK_CREATED,
                description=description,
                target_entity_type="task",
                target_entity_id=999,  # Fake task ID for testing
                activity_data={
                    "task_name": task_name,
                    "task_priority": "HIGH",
                    "task_status": "NOT_STARTED",
                    "test_source": "ui_test_script"
                }
            )
            
            print(f"✅ Created new activity: {activity.id}")
            print(f"   Description: {description}")
            print(f"   Activity Type: {activity.activity_type}")
            
            # Now get recent activities to verify it appears
            print(f"\n🔍 Getting recent activities after creation...")
            activities = await ActivityService.get_recent_activities(db, project_id, limit=5)
            
            print(f"Found {len(activities)} recent activities:")
            for i, act in enumerate(activities, 1):
                print(f"{i}. {act['activity_type']}: {act['description']}")
                print(f"   By: {act['user']['name']} at {act['created_at']}")
                print(f"   Icon: {act['icon']}, Color: {act['color']}")
                if act.get('extra_data'):
                    print(f"   Data: {act['extra_data']}")
                print("-" * 40)
                
            # Check if our new activity is at the top
            if activities and activities[0]['id'] == activity.id:
                print(f"✅ SUCCESS: New activity appears at top of recent activities!")
            else:
                print(f"❌ WARNING: New activity not found at top of recent activities")
                
    except Exception as e:
        print(f"❌ Error testing new task activity: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_new_task_activity())

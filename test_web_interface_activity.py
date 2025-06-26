#!/usr/bin/env python3
"""
Test creating a task activity exactly like the web interface does
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

async def test_web_interface_activity():
    # Load environment variables
    load_dotenv()
    
    # Database connection
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'azazeladmin')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'testdb')}"
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("🔍 Simulating task creation like in web interface...")
            
            project_id = 18
            user_id = 1  # John Manager
            task_name = f"Web Interface Test Task"
            
            # Create activity description exactly like in project_routes.py
            description = f'John Manager created task "{task_name}"'
            
            print(f"Creating activity: {description}")
            print(f"Current time: {datetime.utcnow()}")
            
            # Log activity exactly like the web interface does
            activity = await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=user_id,
                activity_type=ActivityType.TASK_CREATED,
                description=description,
                target_entity_type="task",
                target_entity_id=1001,
                activity_data={
                    "task_name": task_name,
                    "task_priority": "MEDIUM",
                    "task_status": "NOT_STARTED",
                    "source": "web_interface_simulation"
                }
            )
            
            print(f"✅ Activity created with ID: {activity.id}")
            print(f"   Created at: {activity.created_at}")
            
            # Immediately check recent activities
            print(f"\n🔍 Checking recent activities immediately after creation...")
            activities = await ActivityService.get_recent_activities(db, project_id, limit=10)
            
            print(f"Found {len(activities)} activities:")
            print("=" * 80)
            
            for i, act in enumerate(activities, 1):
                is_new = "🆕 " if act['id'] == activity.id else "   "
                print(f"{is_new}{i}. ID {act['id']}: {act['activity_type']}")
                print(f"   {act['description']}")
                print(f"   By: {act['user']['name']} at {act['created_at']}")
                print(f"   Icon: {act['icon']}, Color: {act['color']}")
                print("-" * 80)
            
            # Check positioning
            if activities:
                top_activity = activities[0]
                if top_activity['id'] == activity.id:
                    print(f"\n✅ SUCCESS! New activity is at the top!")
                    print(f"🎉 Activity logging and UI display should work correctly!")
                else:
                    print(f"\n❌ New activity is not at top.")
                    print(f"Top activity: ID {top_activity['id']} - {top_activity['description']}")
                    print(f"Top activity time: {top_activity['created_at']}")
                    print(f"New activity time: {activity.created_at}")
                    
                    # Check if new activity is in the list
                    new_activity_position = None
                    for idx, act in enumerate(activities):
                        if act['id'] == activity.id:
                            new_activity_position = idx + 1
                            break
                    
                    if new_activity_position:
                        print(f"New activity found at position {new_activity_position}")
                    else:
                        print(f"❌ New activity not found in recent activities list!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_web_interface_activity())

#!/usr/bin/env python3
"""
Test activity creation with timezone-aware datetime
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.services.activity_service import ActivityService
from src.models.activity import ActivityType


async def test_timezone_aware_activity():
    # Load environment variables
    load_dotenv()

    # Database connection
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'azazeladmin')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'testdb')}"

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            print("🔍 Testing timezone-aware activity creation...")

            # Show current times
            now_utc = datetime.now(timezone.utc)
            print(f"Current UTC time: {now_utc}")

            project_id = 18
            user_id = 1  # John Manager
            task_name = f"Timezone Test Task {now_utc.strftime('%H:%M:%S')}"

            # Log a new task activity
            description = f'John Manager created task "{task_name}"'

            activity = await ActivityService.log_activity(
                db=db,
                project_id=project_id,
                user_id=user_id,
                activity_type=ActivityType.TASK_CREATED,
                description=description,
                target_entity_type="task",
                target_entity_id=1000,  # Fake task ID for testing
                activity_data={
                    "task_name": task_name,
                    "task_priority": "HIGH",
                    "task_status": "NOT_STARTED",
                    "test_source": "timezone_test",
                    "created_at_utc": str(now_utc),
                },
            )

            print(f"✅ Created new activity: {activity.id}")
            print(f"   Description: {description}")
            print(f"   Created at: {activity.created_at}")

            # Now get recent activities to verify it appears at the top
            print(f"\n🔍 Getting recent activities after timezone-aware creation...")
            activities = await ActivityService.get_recent_activities(
                db, project_id, limit=5
            )

            print(f"Found {len(activities)} recent activities:")
            for i, act in enumerate(activities, 1):
                print(f"{i}. ID {act['id']}: {act['activity_type']}")
                print(f"   Description: {act['description']}")
                print(f"   By: {act['user']['name']} at {act['created_at']}")
                print(f"   Icon: {act['icon']}, Color: {act['color']}")
                print("-" * 50)

            # Check if our new activity is at the top
            if activities and activities[0]["id"] == activity.id:
                print(f"✅ SUCCESS: New timezone-aware activity appears at top!")
                print(f"The activity logging and retrieval is working correctly!")
            else:
                print(
                    f"❌ Still not at top. Top activity ID: {activities[0]['id'] if activities else 'None'}"
                )
                print(f"Expected ID: {activity.id}")

    except Exception as e:
        print(f"❌ Error testing timezone-aware activity: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_timezone_aware_activity())

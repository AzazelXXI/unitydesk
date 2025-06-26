#!/usr/bin/env python3
"""
Test the ActivityService directly to see what it returns
"""
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.services.activity_service import ActivityService

async def test_activity_service():
    # Load environment variables
    load_dotenv()
    
    # Database connection
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'azazeladmin')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'testdb')}"
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("🔍 Testing ActivityService.get_recent_activities()")
            
            # Test with project ID 18 (from debug results)
            project_id = 18
            activities = await ActivityService.get_recent_activities(db, project_id, limit=10)
            
            print(f"ActivityService returned {len(activities)} activities:")
            print("-" * 60)
            
            for i, activity in enumerate(activities, 1):
                print(f"{i}. Activity ID: {activity.get('id', 'N/A')}")
                print(f"   Type: {activity.get('activity_type', 'N/A')}")
                print(f"   Description: {activity.get('description', 'N/A')}")
                print(f"   Created: {activity.get('created_at', 'N/A')}")
                print(f"   User: {activity.get('user', {}).get('name', 'N/A')}")
                print(f"   Icon: {activity.get('icon', 'N/A')}")
                print(f"   Color: {activity.get('color', 'N/A')}")
                print(f"   Extra Data: {activity.get('extra_data', 'N/A')}")
                print("-" * 40)
                
            if not activities:
                print("❌ No activities returned by ActivityService!")
            else:
                print(f"✅ ActivityService returned {len(activities)} activities successfully")
                
    except Exception as e:
        print(f"❌ Error testing ActivityService: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_activity_service())

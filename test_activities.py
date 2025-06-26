#!/usr/bin/env python3
"""
Test script to debug and fix activity functionality in the CSA Platform.
This script will:
1. Check if the project_activities table exists and has the correct structure
2. Insert some test activities
3. Test the ActivityService.get_recent_activities method
4. Check if activities are being displayed properly
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import json

from src.models.activity import ProjectActivity, ActivityType
from src.services.activity_service import ActivityService
from src.models.user import User
from src.models.project import Project

# Import the database configuration from the application
try:
    from src.database import DATABASE_URL
    print(f"✅ Using application DATABASE_URL")
except ImportError:
    # Fallback to direct .env reading
    try:
        from dotenv import load_dotenv
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:azazeladmin@localhost:5432/testdb")
        print(f"✅ Using .env DATABASE_URL")
    except ImportError:
        # Final fallback
        DATABASE_URL = "postgresql+asyncpg://postgres:azazeladmin@localhost:5432/testdb"
        print(f"⚠️  Using hardcoded DATABASE_URL")

async def test_activities():
    """Test the activity functionality"""
    
    print("=" * 60)
    print("CSA PLATFORM - ACTIVITY FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Step 1: Check if project_activities table exists
            print("\n1. Checking project_activities table structure...")
            table_check = await db.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'project_activities' 
                ORDER BY ordinal_position
            """))
            columns = table_check.fetchall()
            
            if not columns:
                print("❌ ERROR: project_activities table does not exist!")
                return
            
            print("✅ project_activities table structure:")
            for col in columns:
                print(f"  - {col.column_name}: {col.data_type} ({'NULL' if col.is_nullable == 'YES' else 'NOT NULL'})")
            
            # Step 2: Get first project and user for testing
            print("\n2. Finding test project and user...")
            project_result = await db.execute(text("SELECT id, name FROM projects LIMIT 1"))
            project_row = project_result.fetchone()
            
            user_result = await db.execute(text("SELECT id, name FROM users LIMIT 1"))
            user_row = user_result.fetchone()
            
            if not project_row or not user_row:
                print("❌ ERROR: Need at least one project and one user in the database!")
                return
            
            project_id = project_row.id
            user_id = user_row.id
            print(f"✅ Using project: {project_row.name} (ID: {project_id})")
            print(f"✅ Using user: {user_row.name} (ID: {user_id})")
            
            # Step 3: Check existing activities
            print(f"\n3. Checking existing activities for project {project_id}...")
            existing_activities = await db.execute(text("""
                SELECT id, activity_type, description, created_at 
                FROM project_activities 
                WHERE project_id = :project_id 
                ORDER BY created_at DESC 
                LIMIT 5
            """), {"project_id": project_id})
            
            activities = existing_activities.fetchall()
            print(f"✅ Found {len(activities)} existing activities:")
            for activity in activities:
                print(f"  - [{activity.created_at}] {activity.activity_type}: {activity.description}")
            
            # Step 4: Test ActivityService.log_activity method
            print(f"\n4. Testing ActivityService.log_activity method...")
            try:
                test_description = f"Test activity created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                await ActivityService.log_activity(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    activity_type=ActivityType.TASK_CREATED,
                    description=test_description,
                    target_entity_type="task",
                    target_entity_id=999,  # Fake task ID for testing
                    extra_data={
                        "task_name": "Test Task",
                        "test_flag": True
                    }
                )
                print("✅ ActivityService.log_activity executed successfully")
            except Exception as e:
                print(f"❌ ERROR in ActivityService.log_activity: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Step 5: Test ActivityService.get_recent_activities method
            print(f"\n5. Testing ActivityService.get_recent_activities method...")
            try:
                recent_activities = await ActivityService.get_recent_activities(db, project_id, limit=10)
                print(f"✅ Retrieved {len(recent_activities)} activities:")
                
                for activity in recent_activities:
                    print(f"  - ID: {activity.id}")
                    print(f"    Type: {activity.activity_type}")
                    print(f"    Description: {activity.description}")
                    print(f"    User: {activity.user.name if activity.user else 'Unknown'}")
                    print(f"    Created: {activity.created_at}")
                    print(f"    Icon: {getattr(activity, 'icon', 'N/A')}")
                    print(f"    Color: {getattr(activity, 'color', 'N/A')}")
                    print("    ---")
                    
            except Exception as e:
                print(f"❌ ERROR in ActivityService.get_recent_activities: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Step 6: Insert more test activities directly
            print(f"\n6. Inserting additional test activities...")
            test_activities = [
                {
                    "activity_type": "TASK_UPDATED",
                    "description": f"{user_row.name} updated task 'Sample Task'",
                    "target_entity_type": "task",
                    "target_entity_id": 998
                },
                {
                    "activity_type": "MEMBER_ADDED", 
                    "description": f"{user_row.name} was added to the project",
                    "target_entity_type": "user",
                    "target_entity_id": user_id
                },
                {
                    "activity_type": "PROJECT_UPDATED",
                    "description": f"Project details were updated by {user_row.name}",
                    "target_entity_type": "project", 
                    "target_entity_id": project_id
                }
            ]
            
            for i, activity_data in enumerate(test_activities):
                try:
                    await db.execute(text("""
                        INSERT INTO project_activities 
                        (project_id, user_id, activity_type, description, target_entity_type, target_entity_id, extra_data, created_at)
                        VALUES (:project_id, :user_id, :activity_type, :description, :target_entity_type, :target_entity_id, :extra_data, :created_at)
                    """), {
                        "project_id": project_id,
                        "user_id": user_id,
                        "activity_type": activity_data["activity_type"],
                        "description": activity_data["description"],
                        "target_entity_type": activity_data["target_entity_type"],
                        "target_entity_id": activity_data["target_entity_id"],
                        "extra_data": json.dumps({"test": True, "batch": i + 1}),
                        "created_at": datetime.utcnow()
                    })
                    print(f"✅ Inserted test activity: {activity_data['activity_type']}")
                except Exception as e:
                    print(f"❌ ERROR inserting activity {i+1}: {str(e)}")
            
            await db.commit()
            
            # Step 7: Final verification
            print(f"\n7. Final verification - checking all activities...")
            final_check = await db.execute(text("""
                SELECT 
                    pa.id,
                    pa.activity_type,
                    pa.description,
                    pa.created_at,
                    u.name as user_name
                FROM project_activities pa
                LEFT JOIN users u ON pa.user_id = u.id
                WHERE pa.project_id = :project_id
                ORDER BY pa.created_at DESC
                LIMIT 10
            """), {"project_id": project_id})
            
            final_activities = final_check.fetchall()
            print(f"✅ Final count: {len(final_activities)} activities for project {project_id}")
            
            print(f"\n8. Testing web route compatibility...")
            # Test the same query that's used in project_routes.py
            route_activities = await ActivityService.get_recent_activities(db, project_id, limit=5)
            print(f"✅ Web route would receive {len(route_activities)} activities")
            
            # Check if activities have the required attributes for templates
            for activity in route_activities[:3]:  # Check first 3
                has_icon = hasattr(activity, 'icon') and activity.icon
                has_color = hasattr(activity, 'color') and activity.color
                has_user = hasattr(activity, 'user') and activity.user
                has_description = hasattr(activity, 'description') and activity.description
                has_created_at = hasattr(activity, 'created_at') and activity.created_at
                
                print(f"  Activity {activity.id}:")
                print(f"    - Has icon: {has_icon} ({getattr(activity, 'icon', 'None')})")
                print(f"    - Has color: {has_color} ({getattr(activity, 'color', 'None')})")
                print(f"    - Has user: {has_user}")
                print(f"    - Has description: {has_description}")
                print(f"    - Has created_at: {has_created_at}")
                
                if not all([has_icon, has_color, has_user, has_description, has_created_at]):
                    print(f"    ⚠️  Missing required attributes for template rendering!")
                else:
                    print(f"    ✅ All attributes present for template rendering")
            
            print(f"\n" + "=" * 60)
            print("TEST COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Next steps:")
            print(f"1. Check your web application to see if activities now appear")
            print(f"2. Create a new task or add a member to generate real activities")
            print(f"3. If activities still don't show, check the browser console for errors")
            print(f"4. Verify the project_routes.py is passing activities correctly to templates")
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("Starting CSA Platform Activity Test...")
    print("Make sure your database is running and accessible!")
    print()
    
    try:
        asyncio.run(test_activities())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

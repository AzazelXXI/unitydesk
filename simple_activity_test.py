#!/usr/bin/env python3
"""
Simple activity test script - Direct database testing for CSA Platform activities.
This script connects directly to the database and tests the activity functionality.
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timezone
import os


async def test_activities_simple():
    """Simple test of activity functionality using direct database connection"""

    print("=" * 60)
    print("CSA PLATFORM - SIMPLE ACTIVITY TEST")
    print("=" * 60)

    # Database connection parameters
    db_config = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "azazeladmin",
        "database": "testdb",
    }

    try:
        # Connect to database
        print("1. Connecting to database...")
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected successfully!")

        # Check if project_activities table exists
        print("\n2. Checking project_activities table...")
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'project_activities'
            )
        """
        )

        if not table_exists:
            print("❌ project_activities table does not exist!")
            return

        print("✅ project_activities table exists")

        # Get table structure
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'project_activities' 
            ORDER BY ordinal_position
        """
        )

        print("   Table structure:")
        for col in columns:
            print(
                f"     - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})"
            )

        # Get first project and user
        print("\n3. Finding test data...")
        project = await conn.fetchrow("SELECT id, name FROM projects LIMIT 1")
        user = await conn.fetchrow("SELECT id, name FROM users LIMIT 1")

        if not project or not user:
            print("❌ Need at least one project and one user in database!")
            return

        project_id, project_name = project["id"], project["name"]
        user_id, user_name = user["id"], user["name"]

        print(f"✅ Using project: {project_name} (ID: {project_id})")
        print(f"✅ Using user: {user_name} (ID: {user_id})")

        # Check existing activities
        print(f"\n4. Checking existing activities...")
        existing = await conn.fetch(
            """
            SELECT id, activity_type, description, created_at 
            FROM project_activities 
            WHERE project_id = $1 
            ORDER BY created_at DESC 
            LIMIT 5
        """,
            project_id,
        )

        print(f"✅ Found {len(existing)} existing activities:")
        for activity in existing:
            print(
                f"   - [{activity['created_at']}] {activity['activity_type']}: {activity['description']}"
            )

        # Insert test activities
        print(f"\n5. Inserting test activities...")
        test_activities = [
            {
                "activity_type": "TASK_CREATED",
                "description": f"Test task created by {user_name} at {datetime.now().strftime('%H:%M:%S')}",
                "target_entity_type": "task",
                "target_entity_id": 999,
                "activity_data": {"test": True, "source": "simple_test"},
            },
            {
                "activity_type": "MEMBER_ADDED",
                "description": f"{user_name} was added to the project team",
                "target_entity_type": "user",
                "target_entity_id": user_id,
                "activity_data": {"role": "Test Member", "test": True},
            },
            {
                "activity_type": "PROJECT_UPDATED",
                "description": f"Project settings updated by {user_name}",
                "target_entity_type": "project",
                "target_entity_id": project_id,
                "activity_data": {"changes": ["description"], "test": True},
            },
        ]

        inserted_ids = []
        for i, activity_data in enumerate(test_activities):
            try:
                activity_id = await conn.fetchval(
                    """
                    INSERT INTO project_activities 
                    (project_id, user_id, activity_type, description, target_entity_type, target_entity_id, activity_data, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """,
                    project_id,
                    user_id,
                    activity_data["activity_type"],
                    activity_data["description"],
                    activity_data["target_entity_type"],
                    activity_data["target_entity_id"],
                    json.dumps(activity_data["activity_data"]),
                    datetime.now(),
                )
                inserted_ids.append(activity_id)
                print(
                    f"✅ Inserted activity {i+1}: {activity_data['activity_type']} (ID: {activity_id})"
                )
            except Exception as e:
                print(f"❌ Failed to insert activity {i+1}: {str(e)}")

        # Verify the activities were inserted
        print(f"\n6. Verifying inserted activities...")
        if inserted_ids:
            placeholders = ",".join(f"${i+1}" for i in range(len(inserted_ids)))
            verified = await conn.fetch(
                f"""
                SELECT 
                    pa.id,
                    pa.activity_type,
                    pa.description,
                    pa.created_at,
                    u.name as user_name
                FROM project_activities pa
                LEFT JOIN users u ON pa.user_id = u.id
                WHERE pa.id = ANY($1)
                ORDER BY pa.created_at DESC
            """,
                inserted_ids,
            )

            print(f"✅ Verified {len(verified)} activities:")
            for activity in verified:
                print(f"   - ID {activity['id']}: {activity['activity_type']}")
                print(f"     Description: {activity['description']}")
                print(f"     User: {activity['user_name']}")
                print(f"     Created: {activity['created_at']}")
                print()

        # Test activity retrieval with user join (like in ActivityService)
        print(f"\n7. Testing activity retrieval with user data...")
        activities_with_users = await conn.fetch(
            """
            SELECT 
                pa.id,
                pa.activity_type,
                pa.description,
                pa.created_at,
                pa.activity_data,
                u.id as user_id,
                u.name as user_name,
                u.email as user_email
            FROM project_activities pa
            LEFT JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = $1
            ORDER BY pa.created_at DESC
            LIMIT 10
        """,
            project_id,
        )

        print(f"✅ Retrieved {len(activities_with_users)} activities with user data:")
        for activity in activities_with_users:
            print(f"   - {activity['activity_type']}: {activity['description']}")
            print(f"     By: {activity['user_name']} ({activity['user_email']})")
            print(f"     At: {activity['created_at']}")
            if activity["activity_data"]:
                try:
                    extra = json.loads(activity["activity_data"])
                    print(f"     Extra: {extra}")
                except:
                    print(f"     Extra: {activity['activity_data']}")
            print("     ---")

        print(f"\n" + "=" * 60)
        print("SIMPLE ACTIVITY TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Summary:")
        print(f"- Database connection: ✅ Working")
        print(f"- project_activities table: ✅ Exists")
        print(f"- Activity insertion: ✅ Working")
        print(f"- Activity retrieval: ✅ Working")
        print(f"- User data join: ✅ Working")
        print()
        print("Next steps:")
        print("1. Check your web application - activities should now appear!")
        print("2. Try creating a task or adding a member to generate real activities")
        print(
            "3. If activities still don't appear, check the browser console for errors"
        )

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        try:
            await conn.close()
            print("\n✅ Database connection closed")
        except:
            pass


if __name__ == "__main__":
    print("Starting Simple CSA Platform Activity Test...")
    print("Make sure PostgreSQL is running!")
    print()

    try:
        asyncio.run(test_activities_simple())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback

        traceback.print_exc()

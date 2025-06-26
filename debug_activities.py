#!/usr/bin/env python3
"""
Debug activity retrieval - check what activities are in the database and what the service returns
"""
import asyncio
import asyncpg
import os
import json
from dotenv import load_dotenv


async def debug_activities():
    # Load environment variables
    load_dotenv()

    # Database connection parameters
    db_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "azazeladmin"),
        "database": os.getenv("DB_NAME", "testdb"),
    }

    try:
        # Connect to database
        conn = await asyncpg.connect(**db_params)
        print(f"✅ Connected to database: {db_params['database']}")

        # Get all projects to test with
        projects = await conn.fetch("SELECT id, name FROM projects ORDER BY id LIMIT 3")
        if not projects:
            print("❌ No projects found in database")
            return

        print(f"Found {len(projects)} projects:")
        for proj in projects:
            print(f"  - Project {proj['id']}: {proj['name']}")

        # Use the first project for testing
        project_id = projects[0]["id"]
        print(
            f"\n🔍 Debugging activities for project {project_id}: {projects[0]['name']}"
        )

        # Check raw activities in database
        print("\n1. Raw activities from database:")
        raw_activities = await conn.fetch(
            """
            SELECT 
                id, project_id, user_id, activity_type, description, 
                target_entity_type, target_entity_id, activity_data, created_at
            FROM project_activities 
            WHERE project_id = $1 
            ORDER BY created_at DESC 
            LIMIT 10
        """,
            project_id,
        )

        if raw_activities:
            print(f"   Found {len(raw_activities)} raw activities:")
            for act in raw_activities:
                print(
                    f"   - ID {act['id']}: {act['activity_type']} - {act['description']}"
                )
                print(f"     User ID: {act['user_id']}, Created: {act['created_at']}")
                if act["activity_data"]:
                    try:
                        data = (
                            json.loads(act["activity_data"])
                            if isinstance(act["activity_data"], str)
                            else act["activity_data"]
                        )
                        print(f"     Data: {data}")
                    except:
                        print(f"     Data: {act['activity_data']}")
        else:
            print("   ❌ No activities found for this project")

        # Check activities with user join (like the service does)
        print("\n2. Activities with user data (like ActivityService):")
        service_activities = await conn.fetch(
            """
            SELECT 
                pa.id,
                pa.activity_type,
                pa.description,
                pa.target_entity_type,
                pa.target_entity_id,
                pa.activity_data,
                pa.created_at,
                u.id as user_id,
                u.name as user_name,
                u.email as user_email
            FROM project_activities pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = $1
            ORDER BY pa.created_at DESC
            LIMIT 10
        """,
            project_id,
        )

        if service_activities:
            print(f"   Found {len(service_activities)} activities with user data:")
            for act in service_activities:
                print(f"   - {act['activity_type']}: {act['description']}")
                print(f"     By: {act['user_name']} (ID: {act['user_id']})")
                print(f"     Created: {act['created_at']}")
        else:
            print("   ❌ No activities found with user join")

        # Check if there are any recent activities (last hour)
        print("\n3. Recent activities (last hour):")
        recent_activities = await conn.fetch(
            """
            SELECT 
                pa.id, pa.activity_type, pa.description, pa.created_at,
                u.name as user_name
            FROM project_activities pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = $1 
            AND pa.created_at > NOW() - INTERVAL '1 hour'
            ORDER BY pa.created_at DESC
        """,
            project_id,
        )

        if recent_activities:
            print(f"   Found {len(recent_activities)} recent activities:")
            for act in recent_activities:
                print(f"   - {act['activity_type']}: {act['description']}")
                print(f"     By: {act['user_name']}, At: {act['created_at']}")
        else:
            print("   ℹ️  No activities in the last hour")

        # Check all users to see if there are any user ID mismatches
        print("\n4. Checking users:")
        users = await conn.fetch("SELECT id, name, email FROM users ORDER BY id")
        print(f"   Found {len(users)} users:")
        for user in users:
            print(f"   - User {user['id']}: {user['name']} ({user['email']})")

        await conn.close()
        print(f"\n" + "=" * 60)
        print("DEBUG COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_activities())

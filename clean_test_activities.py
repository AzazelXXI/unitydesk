#!/usr/bin/env python3
"""
Clean up test activities with incorrect future timestamps
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv


async def clean_test_activities():
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

        project_id = 18

        # Show current activities before cleanup
        print(f"\n📋 Current activities before cleanup:")
        activities_before = await conn.fetch(
            """
            SELECT 
                pa.id, pa.activity_type, pa.description, pa.created_at,
                u.name as user_name
            FROM project_activities pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = $1
            ORDER BY pa.created_at DESC
        """,
            project_id,
        )

        for act in activities_before:
            print(f"   ID {act['id']}: {act['description']} - {act['created_at']}")

        # Delete test activities with future timestamps or test markers
        print(f"\n🧹 Cleaning up test activities...")

        # Delete activities that are clearly test activities
        deleted_count = await conn.execute(
            """
            DELETE FROM project_activities 
            WHERE project_id = $1 
            AND (
                created_at > NOW() OR  -- Future timestamps
                description LIKE '%Test task created by Sarah Leader%' OR  -- Test descriptions
                description LIKE '%Project settings updated by Sarah Leader%' OR
                description LIKE '%Sarah Leader was added to the project team%' OR
                activity_data::text LIKE '%"test": true%'  -- Test data
            )
        """,
            project_id,
        )

        print(f"✅ Deleted {deleted_count} test activities")

        # Show remaining activities
        print(f"\n📋 Remaining activities after cleanup:")
        activities_after = await conn.fetch(
            """
            SELECT 
                pa.id, pa.activity_type, pa.description, pa.created_at,
                u.name as user_name
            FROM project_activities pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = $1
            ORDER BY pa.created_at DESC
            LIMIT 10
        """,
            project_id,
        )

        if activities_after:
            for act in activities_after:
                print(f"   ID {act['id']}: {act['description']} - {act['created_at']}")
        else:
            print("   No activities remaining")

        await conn.close()
        print(f"\n✅ Cleanup completed!")

    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(clean_test_activities())

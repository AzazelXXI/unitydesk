#!/usr/bin/env python3
"""
Check the current database schema for project_activities table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv


async def check_schema():
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

        # Check if project_activities table exists
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'project_activities'
            )
        """
        )

        if not table_exists:
            print("❌ project_activities table does not exist")
            return

        print("✅ project_activities table exists")

        # Get column information
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'project_activities'
            ORDER BY ordinal_position
        """
        )

        print(f"\nColumn information for project_activities table:")
        print("-" * 60)
        for col in columns:
            print(
                f"  {col['column_name']:<20} | {col['data_type']:<15} | Nullable: {col['is_nullable']}"
            )
        print("-" * 60)

        # Check specifically for metadata vs activity_data vs extra_data
        column_names = [col["column_name"] for col in columns]

        if "metadata" in column_names:
            print("⚠️  Found 'metadata' column - this needs to be renamed!")
        elif "activity_data" in column_names:
            print("✅ Found 'activity_data' column - matches our model!")
        elif "extra_data" in column_names:
            print("⚠️  Found 'extra_data' column - model expects 'activity_data'")
        else:
            print("❌ No metadata/activity_data/extra_data column found!")

        await conn.close()

    except Exception as e:
        print(f"❌ Error checking database schema: {str(e)}")


if __name__ == "__main__":
    asyncio.run(check_schema())

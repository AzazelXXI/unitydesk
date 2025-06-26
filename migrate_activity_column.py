#!/usr/bin/env python3
"""
Database migration script to rename metadata column to activity_data
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv


async def migrate_column():
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

        # Check current column structure
        columns = await conn.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'project_activities'
        """
        )

        column_names = [col["column_name"] for col in columns]
        print(f"Current columns: {column_names}")

        # Determine what migration is needed
        if "metadata" in column_names:
            print("📋 Migration needed: metadata -> activity_data")
            await conn.execute(
                """
                ALTER TABLE project_activities 
                RENAME COLUMN metadata TO activity_data
            """
            )
            print("✅ Successfully renamed metadata to activity_data")

        elif "extra_data" in column_names:
            print("📋 Migration needed: extra_data -> activity_data")
            await conn.execute(
                """
                ALTER TABLE project_activities 
                RENAME COLUMN extra_data TO activity_data
            """
            )
            print("✅ Successfully renamed extra_data to activity_data")

        elif "activity_data" in column_names:
            print("✅ Column already correctly named as activity_data")

        else:
            print("❌ No metadata/extra_data column found to rename!")
            # Create the column if it doesn't exist
            print("🔧 Adding missing activity_data column...")
            await conn.execute(
                """
                ALTER TABLE project_activities 
                ADD COLUMN activity_data JSONB
            """
            )
            print("✅ Added activity_data column")

        await conn.close()
        print("✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")


if __name__ == "__main__":
    asyncio.run(migrate_column())

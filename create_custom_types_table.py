#!/usr/bin/env python3
"""
Create custom_user_types table manually
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

from src.database import get_db
from sqlalchemy import text


async def create_custom_user_types_table():
    """Create the custom_user_types table manually"""
    print("🔧 Creating custom_user_types table...")

    async for db in get_db():
        try:
            # Create the custom_user_types table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS custom_user_types (
                id SERIAL PRIMARY KEY,
                type_name VARCHAR(100) UNIQUE NOT NULL,
                display_name VARCHAR(255) NOT NULL,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """

            await db.execute(text(create_table_sql))

            # Create index for active user types
            create_index_sql = """
            CREATE INDEX IF NOT EXISTS ix_custom_user_types_is_active 
            ON custom_user_types (is_active);
            """

            await db.execute(text(create_index_sql))

            await db.commit()
            print("✅ Custom user types table created successfully!")

        except Exception as e:
            print(f"❌ Error creating table: {str(e)}")
            await db.rollback()

        break


if __name__ == "__main__":
    asyncio.run(create_custom_user_types_table())

#!/usr/bin/env python3
"""
Script to check the current database schema using a synchronous connection.
This avoids the AsyncEngine inspection issue.
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


def get_sync_engine():
    """Create a synchronous engine from the async database URL."""
    # Get the async database URL from environment
    async_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/csa_hello")

    # Convert asyncpg to psycopg2 for sync connection
    if "asyncpg" in async_url:
        sync_url = async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    else:
        sync_url = async_url

    return create_engine(sync_url)


def check_custom_project_statuses_table():
    """Check the schema of the custom_project_statuses table."""
    engine = get_sync_engine()

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)

            # Check if table exists
            tables = inspector.get_table_names()
            print(f"All tables in database: {tables}")

            if "custom_project_statuses" not in tables:
                print("❌ custom_project_statuses table does not exist!")
                return

            print("\n✅ custom_project_statuses table exists")

            # Get column information
            columns = inspector.get_columns("custom_project_statuses")
            print(f"\nColumns in custom_project_statuses table:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")

            # Check specifically for sort_order column
            column_names = [col["name"] for col in columns]
            if "sort_order" in column_names:
                print("\n⚠️  WARNING: sort_order column still exists in database!")
                print(
                    "   The migration to drop this column has not been applied successfully."
                )
            else:
                print(
                    "\n✅ sort_order column has been successfully removed from database"
                )

            # Get indexes
            indexes = inspector.get_indexes("custom_project_statuses")
            print(f"\nIndexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")

            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys("custom_project_statuses")
            print(f"\nForeign keys:")
            for fk in foreign_keys:
                print(
                    f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                )

            # Check current data
            result = conn.execute(text("SELECT COUNT(*) FROM custom_project_statuses"))
            count = result.scalar()
            print(f"\nTotal records in custom_project_statuses: {count}")

            if count > 0:
                # Show sample data
                result = conn.execute(
                    text(
                        """
                    SELECT id, status_name, display_name, project_id, is_active, is_final, is_custom 
                    FROM custom_project_statuses 
                    LIMIT 5
                """
                    )
                )
                print("\nSample data:")
                for row in result:
                    print(
                        f"  ID: {row[0]}, Name: {row[1]}, Display: {row[2]}, Project: {row[3]}, Active: {row[4]}, Final: {row[5]}, Custom: {row[6]}"
                    )

    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False

    return True


def check_alembic_version():
    """Check the current Alembic version in the database."""
    engine = get_sync_engine()

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)

            if "alembic_version" not in inspector.get_table_names():
                print("❌ alembic_version table does not exist!")
                return

            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"\nCurrent Alembic version: {version}")

            # Check migration history
            result = conn.execute(
                text(
                    """
                SELECT version_num FROM alembic_version 
                ORDER BY version_num
            """
                )
            )
            versions = [row[0] for row in result]
            print(f"All applied versions: {versions}")

    except Exception as e:
        print(f"❌ Error checking Alembic version: {e}")


def main():
    print("🔍 Checking database schema...")
    print("=" * 50)

    # Check if we can connect
    try:
        engine = get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # Check the table schema
    check_custom_project_statuses_table()

    # Check Alembic version
    check_alembic_version()

    print("\n" + "=" * 50)
    print("Schema check complete!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to debug the task query issue
"""
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database import get_db


async def test_task_query():
    """Test the task query that's failing in the API"""

    # Get database session
    async for db in get_db():
        try:
            print("=== Testing Database Connection ===")

            # Test 1: Check if tasks table exists and has data
            print("\n1. Checking tasks table structure...")
            table_check = text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tasks'"
            )
            result = await db.execute(table_check)
            columns = result.fetchall()

            if not columns:
                print("❌ Tasks table not found!")
                return

            print("✅ Tasks table columns:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")

            # Test 2: Check if there are any tasks
            print("\n2. Checking task count...")
            count_query = text("SELECT COUNT(*) FROM tasks")
            result = await db.execute(count_query)
            count = result.scalar()
            print(f"✅ Total tasks in database: {count}")

            if count == 0:
                print("❌ No tasks found in database!")
                return

            # Test 3: List all task IDs
            print("\n3. Listing all task IDs...")
            ids_query = text("SELECT id, name FROM tasks ORDER BY id LIMIT 10")
            result = await db.execute(ids_query)
            rows = result.fetchall()
            print("✅ Available tasks:")
            for row in rows:
                print(f"   - ID: {row[0]}, Name: {row[1]}")

            # Test 4: Check if task ID 11 exists
            print("\n4. Checking if task ID 11 exists...")
            task11_query = text("SELECT id, name FROM tasks WHERE id = 11")
            result = await db.execute(task11_query)
            task11 = result.fetchone()

            if task11:
                print(f"✅ Task 11 found: {task11[1]}")
            else:
                print("❌ Task 11 not found!")

                # Find a valid task ID to test with
                if rows:
                    test_id = rows[0][0]
                    print(f"📝 Suggestion: Use task ID {test_id} for testing instead")
                return

            # Test 5: Try the exact query from the API
            print("\n5. Testing the exact API query...")
            api_query = text(
                """
                SELECT 
                    t.id,
                    t.name,
                    t.description,
                    t.status,
                    t.priority,
                    t.due_date,
                    t.created_at,
                    t.updated_at,
                    t.estimated_hours,
                    t.actual_hours,
                    t.project_id,
                    p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.id = :task_id
            """
            )

            # Test with mappings() method
            print("   Testing with mappings()...")
            result = await db.execute(api_query, {"task_id": 11})
            task_row = result.mappings().fetchone()

            if task_row:
                print("✅ Query successful with mappings()!")
                print("   Task data:")
                for key, value in task_row.items():
                    print(f"     {key}: {value}")
            else:
                print("❌ Query failed with mappings()")

            # Test without mappings() method
            print("   Testing without mappings()...")
            result = await db.execute(api_query, {"task_id": 11})
            task_row = result.fetchone()

            if task_row:
                print("✅ Query successful without mappings()!")
                print(f"   Task data (tuple): {task_row}")
            else:
                print("❌ Query failed without mappings()")

        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback

            traceback.print_exc()

        finally:
            await db.close()
            break


async def main():
    """Main function"""
    print("Starting database query test...")
    await test_task_query()
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(main())

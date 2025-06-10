#!/usr/bin/env python3
"""
Test script to exactly mimic the API endpoint behavior
"""
import asyncio
import sys
import os
import json

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database import get_db


async def test_exact_api_behavior():
    """Test the exact same behavior as the API endpoint"""

    # Get database session
    async for db in get_db():
        try:
            print("=== Testing Exact API Behavior ===")

            task_id = 11

            # Use the EXACT same query from the API
            task_query = text(
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

            print(f"Executing query for task_id: {task_id}")
            result = await db.execute(task_query, {"task_id": task_id})
            task_row = result.mappings().fetchone()

            print(f"Query result: {task_row}")

            if not task_row:
                print("❌ Task not found")
                return

            print("✅ Task found, building response data...")

            # Use the EXACT same data processing from the API
            task_data = {
                "id": task_row["id"] if task_row["id"] is not None else task_id,
                "title": task_row["name"] or f"Task {task_id}",
                "name": task_row["name"] or f"Task {task_id}",
                "description": task_row["description"] or "No description provided",
                "status": task_row["status"] or "unknown",
                "priority": task_row["priority"] or "medium",
                "due_date": (
                    task_row["due_date"].isoformat() if task_row["due_date"] else None
                ),
                "created_at": (
                    task_row["created_at"].isoformat()
                    if task_row["created_at"]
                    else None
                ),
                "updated_at": (
                    task_row["updated_at"].isoformat()
                    if task_row["updated_at"]
                    else None
                ),
                "estimated_hours": task_row["estimated_hours"],
                "actual_hours": task_row["actual_hours"],
                "assignee": {"id": None, "name": "Unassigned", "initials": "??"},
                "project": {
                    "id": task_row["project_id"],
                    "name": task_row["project_name"] or "Unknown Project",
                },
            }

            print("✅ Task data built successfully!")
            print("📋 Final response:")
            print(json.dumps(task_data, indent=2, default=str))

        except Exception as e:
            print(f"❌ Error during API simulation: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback

            traceback.print_exc()

        finally:
            await db.close()
            break


async def main():
    """Main function"""
    print("Starting API behavior test...")
    await test_exact_api_behavior()
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(main())

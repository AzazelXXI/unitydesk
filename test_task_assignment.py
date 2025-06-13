#!/usr/bin/env python3
"""
Test file for task assignment functionality
This file tests the task assignment API endpoints and database connectivity
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import the application and database components
try:
    from src.main import app
    from src.database import get_db, engine
    from src.models.user import User
    from src.models.task import Task

    print("✅ Successfully imported application modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)


def test_database_connection():
    """Test basic database connectivity"""
    print("\n🔍 Testing database connection...")

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_database_tables():
    """Test if required tables exist"""
    print("\n🔍 Testing database tables...")

    tables_to_check = ["users", "user_profiles", "simple_tasks", "task_assignees"]

    try:
        with engine.connect() as connection:
            for table in tables_to_check:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"✅ Table '{table}' exists with {count} records")
                except Exception as e:
                    print(f"❌ Table '{table}' issue: {e}")

            # Check table structure for user_profiles
            try:
                result = connection.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns WHERE table_name = 'user_profiles'"
                    )
                )
                columns = [row[0] for row in result.fetchall()]
                print(f"📋 user_profiles columns: {columns}")
            except Exception as e:
                print(f"❌ Could not get user_profiles structure: {e}")

    except Exception as e:
        print(f"❌ Database table check failed: {e}")
        return False

    return True


def test_users_api():
    """Test the users API endpoint"""
    print("\n🔍 Testing /api/users endpoint...")

    try:
        client = TestClient(app)
        response = client.get("/api/users")

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            users = response.json()
            print(f"✅ Users API successful - found {len(users)} users")

            # Print first few users for debugging
            if users:
                print("Sample users:")
                for i, user in enumerate(users[:3]):
                    print(f"  {i+1}. {user}")
            else:
                print("⚠️ No users found in database")

        elif response.status_code == 401:
            print("❌ Authentication required for users API")
        else:
            print(f"❌ Users API failed with status {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Users API test failed: {e}")


def test_task_details_api():
    """Test task details API with a sample task"""
    print("\n🔍 Testing task details API...")

    try:
        # First, let's see if there are any tasks
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, title FROM simple_tasks LIMIT 5")
            )
            tasks = result.fetchall()

            if not tasks:
                print("⚠️ No tasks found in database to test with")
                return

            print(f"Found {len(tasks)} tasks to test with:")
            for task in tasks:
                print(f"  - Task {task[0]}: {task[1]}")

            # Test with the first task
            test_task_id = tasks[0][0]

            client = TestClient(app)
            response = client.get(f"/api/simple-tasks/{test_task_id}")

            print(f"Task details API status: {response.status_code}")

            if response.status_code == 200:
                task_data = response.json()
                print("✅ Task details API successful")
                print(
                    f"Task data structure: {json.dumps(task_data, indent=2, default=str)}"
                )
            else:
                print(f"❌ Task details API failed")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Task details API test failed: {e}")


def test_task_assignment_api():
    """Test task assignment API"""
    print("\n🔍 Testing task assignment API...")

    try:
        # Get a task and a user to test with
        with engine.connect() as connection:
            # Get a task
            task_result = connection.execute(
                text("SELECT id FROM simple_tasks LIMIT 1")
            )
            task_row = task_result.fetchone()

            if not task_row:
                print("⚠️ No tasks found to test assignment with")
                return

            task_id = task_row[0]

            # Get a user
            user_result = connection.execute(text("SELECT id FROM users LIMIT 1"))
            user_row = user_result.fetchone()

            if not user_row:
                print("⚠️ No users found to test assignment with")
                return

            user_id = user_row[0]

            print(f"Testing assignment of task {task_id} to user {user_id}")

            client = TestClient(app)

            # Test assignment
            assignment_data = {"assignee_id": user_id}
            response = client.put(
                f"/api/simple-tasks/{task_id}/assign",
                json=assignment_data,
                headers={"Content-Type": "application/json"},
            )

            print(f"Assignment API status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ Task assignment API successful")
                print(f"Assignment result: {json.dumps(result, indent=2, default=str)}")
            else:
                print(f"❌ Task assignment API failed")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Task assignment API test failed: {e}")


def test_database_query():
    """Test the specific query used in the task details API"""
    print("\n🔍 Testing task details database query...")

    try:
        with engine.connect() as connection:
            # Get a sample task ID
            task_result = connection.execute(
                text("SELECT id FROM simple_tasks LIMIT 1")
            )
            task_row = task_result.fetchone()

            if not task_row:
                print("⚠️ No tasks found to test query with")
                return

            task_id = task_row[0]

            # Test the query that's causing issues
            query = text(
                """
                SELECT 
                    st.*,
                    u.username as assignee_username,
                    up.display_name as assignee_display_name,
                    up.first_name as assignee_first_name,
                    up.last_name as assignee_last_name
                FROM simple_tasks st
                LEFT JOIN task_assignees ta ON st.id = ta.task_id
                LEFT JOIN users u ON ta.user_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE st.id = :task_id
            """
            )

            result = connection.execute(query, {"task_id": task_id})
            row = result.fetchone()

            if row:
                print("✅ Task details query successful")
                print(f"Query result columns: {result.keys()}")
                print(f"Sample data: {dict(row._mapping)}")
            else:
                print("⚠️ Query returned no results")

    except Exception as e:
        print(f"❌ Task details query failed: {e}")

        # Try a simpler query to isolate the issue
        try:
            with engine.connect() as connection:
                simple_query = text("SELECT * FROM simple_tasks WHERE id = :task_id")
                result = connection.execute(simple_query, {"task_id": task_id})
                row = result.fetchone()

                if row:
                    print("✅ Simple task query works")
                    print(f"Task data: {dict(row._mapping)}")
                else:
                    print("❌ Even simple task query failed")

        except Exception as e2:
            print(f"❌ Simple task query also failed: {e2}")


def main():
    """Run all tests"""
    print("🧪 Starting Task Assignment Functionality Tests")
    print("=" * 60)

    # Test database connectivity
    if not test_database_connection():
        print("\n❌ Database connection failed. Cannot continue with tests.")
        return

    # Test database tables
    test_database_tables()

    # Test specific database query
    test_database_query()

    # Test API endpoints
    test_users_api()
    test_task_details_api()
    test_task_assignment_api()

    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    print(
        "\nIf you see any ❌ errors above, those indicate issues that need to be fixed."
    )
    print("If you see ✅ success messages, those parts are working correctly.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Fixed Async Test file for task assignment functionality
This file tests the task assignment API endpoints and database connectivity with async support
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import asyncpg
import aiohttp

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "database": "testdb",
    "user": "postgres",
    "password": "azazeladmin",
    "port": 5432,
}

# API base URL
API_BASE_URL = "http://localhost:8000"


async def test_database_schema():
    """Test if user_profiles table exists and has correct structure"""
    print("\n🔍 Testing database schema...")

    conn = None
    try:
        # Connect to database asynchronously
        conn = await asyncpg.connect(**DB_CONFIG)

        # Check if user_profiles table exists
        result = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_profiles'
        """
        )

        if not result:
            print("❌ user_profiles table does not exist!")
            return False

        print("✅ user_profiles table exists")

        # Check table structure
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_profiles'
            ORDER BY ordinal_position
        """
        )

        print("📋 user_profiles table structure:")
        for col in columns:
            print(
                f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})"
            )

        # Check if task_assignees table exists
        result = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'task_assignees'
        """
        )

        if not result:
            print("❌ task_assignees table does not exist!")
            return False

        print("✅ task_assignees table exists")

        # Check task_assignees structure
        columns = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'task_assignees'
            ORDER BY ordinal_position
        """
        )

        print("📋 task_assignees table structure:")
        for col in columns:
            print(
                f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})"
            )

        return True

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    finally:
        if conn:
            await conn.close()


async def test_database_data():
    """Test database data and relationships"""
    print("\n🔍 Testing database data...")

    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        # Check users
        users = await conn.fetch("SELECT id, username, email FROM users LIMIT 5")
        print(f"📊 Found {len(users)} users:")
        for user in users:
            print(f"  - ID {user['id']}: {user['username']} ({user['email']})")

        # Check tasks
        tasks = await conn.fetch("SELECT id, title, status FROM simple_tasks LIMIT 5")
        print(f"📊 Found {len(tasks)} tasks:")
        for task in tasks:
            print(f"  - ID {task['id']}: {task['title']} (status: {task['status']})")

        # Check current assignments
        assignments = await conn.fetch(
            """
            SELECT ta.task_id, ta.user_id, u.username, st.title
            FROM task_assignees ta
            JOIN users u ON ta.user_id = u.id
            JOIN simple_tasks st ON ta.task_id = st.id
            LIMIT 10
        """
        )

        print(f"📊 Found {len(assignments)} current assignments:")
        for assignment in assignments:
            print(
                f"  - Task '{assignment['title']}' assigned to {assignment['username']}"
            )

        return True

    except Exception as e:
        print(f"❌ Database data check failed: {e}")
        return False
    finally:
        if conn:
            await conn.close()


async def test_users_api():
    """Test the users API endpoint"""
    print("\n🔍 Testing /api/users endpoint...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/api/users") as response:
                status = response.status
                print(f"Status Code: {status}")

                if status == 200:
                    users = await response.json()
                    print(f"✅ Users API successful - found {len(users)} users")

                    # Print first few users for debugging
                    if users:
                        print("Sample users:")
                        for i, user in enumerate(users[:3]):
                            print(f"  {i+1}. {user}")
                    else:
                        print("⚠️ No users found in database")

                elif status == 401:
                    print("❌ Authentication required for users API")
                else:
                    text = await response.text()
                    print(f"❌ Users API failed with status {status}")
                    print(f"Response: {text}")

    except aiohttp.ClientError as e:
        print(f"❌ Users API request failed: {e}")
        print("⚠️ Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Users API test failed: {e}")


async def test_task_details_api():
    """Test task details API with a sample task"""
    print("\n🔍 Testing task details API...")

    conn = None
    try:
        # First get tasks from database
        conn = await asyncpg.connect(**DB_CONFIG)
        tasks = await conn.fetch("SELECT id, title FROM simple_tasks LIMIT 3")

        if not tasks:
            print("⚠️ No tasks found in database to test with")
            return

        print(f"Found {len(tasks)} tasks to test with:")
        for task in tasks:
            print(f"  - Task {task['id']}: {task['title']}")

        # Test with the first task
        test_task_id = tasks[0]["id"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/api/simple-tasks/{test_task_id}"
            ) as response:
                status = response.status
                print(f"Task details API status: {status}")

                if status == 200:
                    task_data = await response.json()
                    print("✅ Task details API successful")
                    print(
                        f"Task data structure: {json.dumps(task_data, indent=2, default=str)}"
                    )
                else:
                    text = await response.text()
                    print(f"❌ Task details API failed")
                    print(f"Response: {text}")

    except Exception as e:
        print(f"❌ Task details API test failed: {e}")
    finally:
        if conn:
            await conn.close()


async def test_task_assignment_api():
    """Test task assignment API"""
    print("\n🔍 Testing task assignment API...")

    conn = None
    try:
        # Get a task and a user to test with
        conn = await asyncpg.connect(**DB_CONFIG)

        # Get a task
        task_result = await conn.fetch("SELECT id, title FROM simple_tasks LIMIT 1")
        if not task_result:
            print("⚠️ No tasks found to test assignment with")
            return

        task_id = task_result[0]["id"]
        task_title = task_result[0]["title"]

        # Get a user
        user_result = await conn.fetch("SELECT id, username FROM users LIMIT 1")
        if not user_result:
            print("⚠️ No users found to test assignment with")
            return

        user_id = user_result[0]["id"]
        username = user_result[0]["username"]

        print(
            f"Testing assignment of task '{task_title}' (ID: {task_id}) to user '{username}' (ID: {user_id})"
        )

        # Test assignment
        assignment_data = {"assignee_id": user_id}

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{API_BASE_URL}/api/simple-tasks/{task_id}/assign",
                json=assignment_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                status = response.status
                print(f"Assignment API status: {status}")

                if status == 200:
                    result = await response.json()
                    print("✅ Task assignment API successful")
                    print(
                        f"Assignment result: {json.dumps(result, indent=2, default=str)}"
                    )
                else:
                    text = await response.text()
                    print(f"❌ Task assignment API failed")
                    print(f"Response: {text}")

    except Exception as e:
        print(f"❌ Task assignment API test failed: {e}")
    finally:
        if conn:
            await conn.close()


async def test_assignment_query():
    """Test the specific query used in the task details API"""
    print("\n🔍 Testing task details with assignment query...")

    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        # Get a sample task ID
        task_result = await conn.fetch("SELECT id FROM simple_tasks LIMIT 1")
        if not task_result:
            print("⚠️ No tasks found to test query with")
            return

        task_id = task_result[0]["id"]

        # Test the query that might be causing issues
        query = """
            SELECT 
                st.*,
                ta.user_id as assignee_id,
                u.username as assignee_username,
                u.email as assignee_email,
                up.display_name as assignee_display_name,
                up.first_name as assignee_first_name,
                up.last_name as assignee_last_name
            FROM simple_tasks st
            LEFT JOIN task_assignees ta ON st.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE st.id = $1
        """

        result = await conn.fetch(query, task_id)

        if result:
            print("✅ Task details with assignment query successful")
            row = result[0]
            # Convert to dict for printing
            row_dict = dict(row)
            print(f"Query result: {json.dumps(row_dict, indent=2, default=str)}")
        else:
            print("⚠️ Query returned no results")

    except Exception as e:
        print(f"❌ Task details query failed: {e}")

        # Try a simpler query to isolate the issue
        try:
            simple_query = "SELECT * FROM simple_tasks WHERE id = $1"
            result = await conn.fetch(simple_query, task_id)

            if result:
                print("✅ Simple task query works")
                row_dict = dict(result[0])
                print(f"Task data: {json.dumps(row_dict, indent=2, default=str)}")
            else:
                print("❌ Even simple task query failed")

        except Exception as e2:
            print(f"❌ Simple task query also failed: {e2}")
    finally:
        if conn:
            await conn.close()


async def create_missing_tables():
    """Create missing tables if they don't exist"""
    print("\n🔧 Checking and creating missing tables...")

    conn = None
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        # Check if task_assignees table exists
        result = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'task_assignees'
        """
        )

        if not result:
            print("⚠️ task_assignees table missing. Creating it...")

            create_table_sql = """
                CREATE TABLE task_assignees (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by INTEGER,
                    FOREIGN KEY (task_id) REFERENCES simple_tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL,
                    UNIQUE(task_id, user_id)
                );
            """

            await conn.execute(create_table_sql)
            print("✅ task_assignees table created successfully")
        else:
            print("✅ task_assignees table already exists")

        # Check if user_profiles table exists
        result = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_profiles'
        """
        )

        if not result:
            print("⚠️ user_profiles table missing. Creating it...")

            create_profile_table_sql = """
                CREATE TABLE user_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    display_name VARCHAR(255),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    bio TEXT,
                    avatar_url VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """

            await conn.execute(create_profile_table_sql)
            print("✅ user_profiles table created successfully")
        else:
            print("✅ user_profiles table already exists")

        return True

    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False
    finally:
        if conn:
            await conn.close()


async def main():
    """Run all tests"""
    print("🧪 Starting Async Task Assignment Functionality Tests")
    print("=" * 70)

    # Test database schema
    schema_ok = await test_database_schema()
    if not schema_ok:
        print("\n⚠️ Some database tables are missing. Attempting to create them...")
        await create_missing_tables()
        # Re-test schema
        await test_database_schema()

    # Test database data
    await test_database_data()

    # Test specific database query
    await test_assignment_query()

    # Test API endpoints (requires server to be running)
    print("\n" + "=" * 70)
    print("🌐 Testing API endpoints (FastAPI server must be running)")
    print("=" * 70)

    await test_users_api()
    await test_task_details_api()
    await test_task_assignment_api()

    print("\n" + "=" * 70)
    print("🏁 Async Test completed!")
    print("\nNext steps:")
    print("1. If you see ❌ errors above, those indicate issues that need to be fixed.")
    print("2. If you see ✅ success messages, those parts are working correctly.")
    print(
        "3. Make sure your FastAPI server is running: python -m uvicorn src.main:app --reload"
    )


if __name__ == "__main__":
    asyncio.run(main())

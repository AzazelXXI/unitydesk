#!/usr/bin/env python3
"""
Test script to verify the create task API works
"""
import asyncio
import sys
import os
import json

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


async def test_create_task_api():
    """Test the create task API endpoint"""
    import httpx

    # Test data for creating a task
    task_data = {
        "title": "Test Task from API",
        "name": "Test Task from API",
        "description": "This is a test task created via API",
        "project_id": 23,  # Using project ID from our earlier test
        "assigned_to_id": 1,
        "status": "NOT_STARTED",
        "priority": "MEDIUM",
        "due_date": "2025-06-30",
        "estimated_hours": 8,
        "category": "Testing",
        "task_type": "Development",
        "is_recurring": False,
    }

    try:
        async with httpx.AsyncClient() as client:
            print("=== Testing Create Task API ===")
            print(f"Task data: {json.dumps(task_data, indent=2)}")

            # Make API call
            response = await client.post(
                "http://localhost:8000/api/simple-tasks/",
                json=task_data,
                headers={"Content-Type": "application/json"},
            )

            print(f"\nAPI Response Status: {response.status_code}")

            if response.status_code == 201:
                result = response.json()
                print("✅ Task created successfully!")
                print(f"Response: {json.dumps(result, indent=2)}")
                return result
            else:
                print("❌ Task creation failed!")
                print(f"Error: {response.text}")
                return None

    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        return None


async def main():
    """Main function"""
    print("Testing Create Task API...")
    result = await test_create_task_api()

    if result:
        print(f"\n🎉 Success! Created task with ID: {result.get('id')}")
    else:
        print("\n💥 Test failed!")


if __name__ == "__main__":
    asyncio.run(main())

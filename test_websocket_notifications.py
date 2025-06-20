"""
Test script for WebSocket notification system
Run this to verify the notification system is working properly
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_websocket_notifications():
    """Test WebSocket connection and message handling"""

    print("🔌 Testing WebSocket Notification System")
    print("=" * 50)

    # Test connection to WebSocket endpoint
    # Replace with your actual server URL and user ID
    websocket_url = "ws://localhost:8000/ws/notifications/1"

    try:
        print(f"📡 Connecting to: {websocket_url}")

        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket connected successfully!")

            # Listen for initial welcome message
            welcome_msg = await websocket.recv()
            welcome_data = json.loads(welcome_msg)
            print(f"📨 Welcome message: {welcome_data}")

            # Send a heartbeat
            heartbeat = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
            await websocket.send(json.dumps(heartbeat))
            print("💓 Heartbeat sent")

            # Listen for heartbeat response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"💓 Heartbeat response: {response_data}")

            # Listen for any incoming notifications for 30 seconds
            print("🔔 Listening for notifications (30 seconds)...")
            print("   (Try updating a task status in another browser tab)")

            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)

                    if data.get("type") == "task_status_update":
                        print(f"🎯 Task notification received!")
                        print(f"   Task: {data['data']['task_title']}")
                        print(
                            f"   Status: {data['data']['old_status']} → {data['data']['new_status']}"
                        )
                        print(f"   Updated by: {data['data']['updated_by']}")
                        print(f"   Message: {data['data']['message']}")
                    else:
                        print(f"📢 Other notification: {data}")

            except asyncio.TimeoutError:
                print("⏰ Timeout reached - no notifications received")

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your FastAPI server is running")
        print("2. Check if the WebSocket endpoint is properly configured")
        print("3. Verify user ID 1 exists in your database")
        print("4. Ensure the user has access to at least one project")


def test_api_endpoints():
    """Test REST API endpoints"""
    import requests

    print("\n🌐 Testing REST API Endpoints")
    print("=" * 50)

    base_url = "http://localhost:8000"

    # Test notification endpoint
    try:
        response = requests.get(f"{base_url}/api/notifications/")
        if response.status_code == 200:
            notifications = response.json()
            print(f"✅ Notifications API: {len(notifications)} notifications found")
        else:
            print(f"⚠️ Notifications API: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Notifications API failed: {e}")

    # Test WebSocket stats
    try:
        response = requests.get(f"{base_url}/ws/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ WebSocket Stats: {stats}")
        else:
            print(f"⚠️ WebSocket Stats: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ WebSocket Stats failed: {e}")

    # Test task API
    try:
        response = requests.get(f"{base_url}/api/tasks/project/1")
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Tasks API: {len(tasks)} tasks found in project 1")
        else:
            print(f"⚠️ Tasks API: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Tasks API failed: {e}")


if __name__ == "__main__":
    print("🧪 WebSocket Notification System Test")
    print("====================================")

    # Test REST APIs first
    test_api_endpoints()

    # Test WebSocket connection
    print("\n▶️ Starting WebSocket test...")
    print("   Make sure your FastAPI server is running on localhost:8000")
    input("   Press Enter to continue...")

    try:
        asyncio.run(test_websocket_notifications())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")

    print("\n✨ Test completed!")
    print("\n📖 To test the full system:")
    print("1. Open http://localhost:8000/projects in your browser")
    print("2. Use the 'Quick Task Status Update' widget")
    print("3. Watch for real-time notifications in the bell icon")
    print("4. Open multiple browser tabs to see cross-tab notifications!")

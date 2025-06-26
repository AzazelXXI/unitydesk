#!/usr/bin/env python3
"""
Test activity creation with proper timestamp
"""
import asyncio
import sys
import os
from datetime import datetime, timezone
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import asyncpg
from dotenv import load_dotenv

async def test_direct_activity_creation():
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'azazeladmin'),
        'database': os.getenv('DB_NAME', 'testdb')
    }
    
    try:
        # Connect to database
        conn = await asyncpg.connect(**db_params)
        print(f"✅ Connected to database: {db_params['database']}")
        
        # Get current time in different formats
        now_utc = datetime.utcnow()
        now_with_tz = datetime.now(timezone.utc)
        
        print(f"Current UTC time (utcnow): {now_utc}")
        print(f"Current UTC time (with timezone): {now_with_tz}")
        
        # Create a test activity directly in the database
        project_id = 18
        user_id = 1
        task_name = f"Direct DB Test {now_utc.strftime('%H:%M:%S')}"
        description = f'John Manager created task "{task_name}"'
        
        activity_data = {
            "task_name": task_name,
            "task_priority": "MEDIUM",
            "task_status": "NOT_STARTED",
            "test_source": "direct_db_test",
            "created_at_test": str(now_utc)
        }
        
        # Insert with explicit timestamp
        activity_id = await conn.fetchval("""
            INSERT INTO project_activities 
            (project_id, user_id, activity_type, description, target_entity_type, target_entity_id, activity_data, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, 
            project_id,
            user_id,
            "TASK_CREATED",
            description,
            "task",
            999,
            json.dumps(activity_data),
            now_utc  # Explicit timestamp
        )
        
        print(f"✅ Created activity with ID: {activity_id}")
        
        # Retrieve it immediately
        created_activity = await conn.fetchrow("""
            SELECT 
                pa.id, pa.activity_type, pa.description, pa.created_at,
                pa.activity_data, u.name as user_name
            FROM project_activities pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.id = $1
        """, activity_id)
        
        if created_activity:
            print(f"✅ Retrieved created activity:")
            print(f"   ID: {created_activity['id']}")
            print(f"   Type: {created_activity['activity_type']}")
            print(f"   Description: {created_activity['description']}")
            print(f"   User: {created_activity['user_name']}")
            print(f"   Created At: {created_activity['created_at']}")
            print(f"   Data: {created_activity['activity_data']}")
        
        # Now check recent activities
        print(f"\n🔍 Checking recent activities...")
        recent = await conn.fetch("""
            SELECT 
                pa.id, pa.activity_type, pa.description, pa.created_at,
                u.name as user_name
            FROM project_activities pa
            JOIN users u ON pa.user_id = u.id
            WHERE pa.project_id = $1
            ORDER BY pa.created_at DESC
            LIMIT 5
        """, project_id)
        
        print(f"Recent activities (top 5):")
        for i, act in enumerate(recent, 1):
            print(f"{i}. ID {act['id']}: {act['activity_type']} - {act['description']}")
            print(f"   By: {act['user_name']}, At: {act['created_at']}")
            print("-" * 40)
        
        # Check if our new activity is at the top
        if recent and recent[0]['id'] == activity_id:
            print(f"✅ SUCCESS: New activity is at the top!")
        else:
            print(f"❌ WARNING: New activity not at top")
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_activity_creation())

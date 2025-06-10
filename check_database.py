#!/usr/bin/env python3

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database import get_db
import os

async def check_database():
    """Check the database for tasks and users"""
    try:
        # Get async database session
        async for db_session in get_db():
            # Check if tasks table exists and what columns it has
            print("=== CHECKING DATABASE SCHEMA ===")
            
            # Check table structure
            schema_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'tasks'
                ORDER BY ordinal_position;
            """)
            schema_result = await db_session.execute(schema_query)
            columns = schema_result.fetchall()
            
            print("Tasks table columns:")
            for col in columns:
                print(f"  - {col.column_name}: {col.data_type}")
            
            # Check if there are any tasks
            count_query = text("SELECT COUNT(*) as count FROM tasks")
            count_result = await db_session.execute(count_query)
            task_count = count_result.fetchone().count
            print(f"\nTotal tasks in database: {task_count}")
            
            # Get a few sample tasks
            if task_count > 0:
                sample_query = text("SELECT id, name, status, priority FROM tasks LIMIT 3")
                sample_result = await db_session.execute(sample_query)
                sample_tasks = sample_result.fetchall()
                
                print("\nSample tasks:")
                for task in sample_tasks:
                    print(f"  ID: {task.id}, Name: {task.name}, Status: {task.status}, Priority: {task.priority}")
            
            # Check users table
            user_count_query = text("SELECT COUNT(*) as count FROM users")
            user_count_result = await db_session.execute(user_count_query)
            user_count = user_count_result.fetchone().count
            print(f"\nTotal users in database: {user_count}")
            
            break  # Only need one session
            
    except Exception as e:
        print(f"Database check failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database())

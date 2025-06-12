from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.database import get_db

router = APIRouter(prefix="/api/simple-tasks", tags=["simple-tasks"])


# Pydantic model for task creation
class SimpleTaskCreate(BaseModel):
    title: str
    name: str
    description: Optional[str] = None
    project_id: int
    assigned_to_id: Optional[int] = None
    status: str = "NOT_STARTED"
    priority: str = "MEDIUM"
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[int] = None
    category: Optional[str] = None
    task_type: Optional[str] = None
    is_recurring: bool = False


@router.get("/{task_id}")
async def get_task_details(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get task details by ID - simple endpoint for task board/list functionality
    """
    try:
        # Use raw SQL with more explicit typing to avoid SQLAlchemy issues
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
        result = await db.execute(task_query, {"task_id": task_id})
        task_row = result.mappings().fetchone()

        if not task_row:
            raise HTTPException(status_code=404, detail="Task not found")

        # Extract data from the row result using dictionary-like access
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
                task_row["created_at"].isoformat() if task_row["created_at"] else None
            ),
            "updated_at": (
                task_row["updated_at"].isoformat() if task_row["updated_at"] else None
            ),
            "estimated_hours": task_row["estimated_hours"],
            "actual_hours": task_row["actual_hours"],
            "assignee": {"id": None, "name": "Unassigned", "initials": "??"},
            "project": {
                "id": task_row["project_id"],
                "name": task_row["project_name"] or "Unknown Project",
            },
        }

        return task_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")

@router.post("/")
async def create_task(task_data: SimpleTaskCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new task - simple endpoint for task creation
    """
    try:
        # Insert task into database using raw SQL
        insert_query = text("""
            INSERT INTO tasks (
                name, description, status, priority, due_date, 
                estimated_hours, project_id, created_at, updated_at
            ) VALUES (
                :name, :description, :status, :priority, :due_date,
                :estimated_hours, :project_id, :created_at, :updated_at
            ) RETURNING id
        """)
        
        # Prepare the data
        current_time = datetime.now()
        query_params = {
            "name": task_data.title or task_data.name,
            "description": task_data.description,
            "status": task_data.status,
            "priority": task_data.priority,
            "due_date": datetime.fromisoformat(task_data.due_date) if task_data.due_date else None,
            "estimated_hours": task_data.estimated_hours,
            "project_id": task_data.project_id,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        result = await db.execute(insert_query, query_params)
        task_id = result.scalar()
        
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        # If there's an assignee, add to task_assignees table
        if task_data.assigned_to_id:
            assignee_query = text("""
                INSERT INTO task_assignees (task_id, user_id, assigned_at)
                VALUES (:task_id, :user_id, :assigned_at)
            """)
            await db.execute(assignee_query, {
                "task_id": task_id,
                "user_id": task_data.assigned_to_id,
                "assigned_at": current_time
            })
        
        await db.commit()
        
        return {
            "id": task_id,
            "message": "Task created successfully",
            "title": task_data.title or task_data.name,
            "status": task_data.status,
            "project_id": task_data.project_id
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

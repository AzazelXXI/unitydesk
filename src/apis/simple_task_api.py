from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database import get_db

router = APIRouter(prefix="/api/simple-tasks", tags=["simple-tasks"])


@router.get("/{task_id}")
async def get_task_details(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get task details by ID - simple endpoint for task board/list functionality
    """    
    try:
        # Use raw SQL with more explicit typing to avoid SQLAlchemy issues
        task_query = text("""
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
        """)
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
            "due_date": task_row["due_date"].isoformat() if task_row["due_date"] else None,
            "created_at": task_row["created_at"].isoformat() if task_row["created_at"] else None,
            "updated_at": task_row["updated_at"].isoformat() if task_row["updated_at"] else None,
            "estimated_hours": task_row["estimated_hours"],
            "actual_hours": task_row["actual_hours"],
            "assignee": {"id": None, "name": "Unassigned", "initials": "??"},
            "project": {
                "id": task_row["project_id"],
                "name": task_row["project_name"] or "Unknown Project"
            }
        }

        return task_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")
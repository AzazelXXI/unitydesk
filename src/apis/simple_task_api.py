from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database import get_db

router = APIRouter(prefix="/api/tasks", tags=["simple-tasks"])


@router.get("/{task_id}")
async def get_task_details(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get task details by ID - simple endpoint for task board/list functionality
    """    try:
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
        task_row = result.fetchone()
        
        if not task_row:
            raise HTTPException(status_code=404, detail="Task not found")

        # Extract data from the row result using column indices or names
        task_data = {
            "id": task_row[0] if task_row[0] is not None else task_id,
            "title": task_row[1] or f"Task {task_id}",
            "name": task_row[1] or f"Task {task_id}",
            "description": task_row[2] or "No description provided",
            "status": task_row[3] or "unknown",
            "priority": task_row[4] or "medium",
            "due_date": task_row[5].isoformat() if task_row[5] else None,
            "created_at": task_row[6].isoformat() if task_row[6] else None,
            "updated_at": task_row[7].isoformat() if task_row[7] else None,
            "estimated_hours": task_row[8],
            "actual_hours": task_row[9],
            "assignee": {"id": None, "name": "Unassigned", "initials": "??"},
            "project": {
                "id": task_row[10],
                "name": task_row[11] or "Unknown Project"
            }
        }

        return task_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")
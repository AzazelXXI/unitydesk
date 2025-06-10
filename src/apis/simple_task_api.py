from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import Optional

from src.database import get_db
from src.models.task import Task
from src.models.user import User
from src.models.project import Project

router = APIRouter(prefix="/api/tasks", tags=["simple-tasks"])

@router.get("/{task_id}")
async def get_task_details(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get task details by ID - simple endpoint for task board/list functionality
    """
    try:
        # Query task with related data
        query = (
            select(Task)
            .filter(Task.id == task_id)
            .options(
                joinedload(Task.project),
                joinedload(Task.assignees)
            )
        )
        
        result = await db.execute(query)
        task = result.scalars().unique().first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get primary assignee (first one if multiple)
        primary_assignee = None
        if task.assignees:
            assignee = task.assignees[0]
            primary_assignee = {
                "id": assignee.id,
                "name": assignee.name,
                "initials": assignee.name[:2].upper() if assignee.name else "??"
            }
        
        # Format response
        return {
            "id": task.id,
            "title": task.name,  # Map name to title for frontend compatibility
            "name": task.name,
            "description": task.description or "No description provided",
            "status": task.status.value if task.status else "unknown",
            "priority": task.priority.value if task.priority else "medium",
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "assignee": primary_assignee or {"id": None, "name": "Unassigned", "initials": "??"},
            "project": {
                "id": task.project.id if task.project else None,
                "name": task.project.name if task.project else "Unknown Project"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")

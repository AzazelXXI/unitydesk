from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi.responses import FileResponse
from pathlib import Path

from src.database import get_db
from src.middleware.auth_middleware import get_current_user_web
from src.models.user import User
from src.services.notification_service import NotificationService
from src.services.websocket_manager import websocket_manager

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


# Pydantic model for task assignment
class TaskAssignmentUpdate(BaseModel):
    assignee_id: Optional[int] = None


# Pydantic model for task comments
class TaskCommentCreate(BaseModel):
    content: str
    # user_id will be automatically set from current_user


class TaskCommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
    task_id: int
    user: dict  # Will contain user info


# Pydantic model for task attachments
class TaskAttachmentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    file_path: str
    created_at: datetime
    user_id: int
    task_id: int
    user: dict  # Will contain user info


# Pydantic model for task status update
class TaskStatusUpdate(BaseModel):
    status: str


@router.get("/users")
async def get_users_for_assignment(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Get all users available for task assignment
    """
    try:
        from src.controllers.task_controller import TaskController

        users = await TaskController.get_users_for_assignment(db)

        # Format users for assignment dropdown
        formatted_users = []
        for user in users:
            formatted_users.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": getattr(user, "email", ""),
                    "initials": user.name[0].upper() if user.name else "?",
                }
            )

        return formatted_users
    except Exception as e:
        print(f"Error fetching users for assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Update task status - for drag and drop functionality
    """
    try:
        # Debug logging
        print(f"🔍 DEBUG: Received status update request")
        print(f"🔍 DEBUG: Task ID = {task_id}")
        print(f"🔍 DEBUG: Status data = {status_data.status}")
        # Validate status (using database enum keys, not values)
        valid_statuses = [
            "NOT_STARTED",
            "IN_PROGRESS",
            "COMPLETED",
            "BLOCKED",
            "CANCELLED",
        ]
        if status_data.status not in valid_statuses:
            print(
                f"🔍 DEBUG: Status validation failed. Received: '{status_data.status}'"
            )
            print(f"🔍 DEBUG: Valid statuses: {valid_statuses}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )        # Check if task exists and get old status
        task_check_query = text("SELECT id, name, status FROM tasks WHERE id = :task_id")
        result = await db.execute(task_check_query, {"task_id": task_id})
        task = result.fetchone()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Store old status for notifications
        old_status = task.status        # Update task status
        update_query = text(
            """
            UPDATE tasks 
            SET status = :status, updated_at = :updated_at 
            WHERE id = :task_id
        """
        )
        
        from datetime import datetime

        now = datetime.now()
        
        await db.execute(
            update_query,
            {"task_id": task_id, "status": status_data.status, "updated_at": now},
        )
        
        await db.commit()

        print(f"✅ Task {task_id} status updated to {status_data.status}")

        # Send notifications only if status actually changed
        if old_status != status_data.status:
            try:
                # Send database notification
                await NotificationService.notify_task_status_change(
                    db=db,
                    task_id=task_id,
                    old_status=old_status,
                    new_status=status_data.status,
                    updated_by_id=current_user.id,
                )

                # Send real-time WebSocket notification
                await websocket_manager.notify_task_status_change(
                    db=db,
                    task_id=task_id,
                    old_status=old_status,
                    new_status=status_data.status,
                    updated_by_user_id=current_user.id,
                )

                print(f"📨 Notifications sent for task {task_id} status change from {old_status} to {status_data.status}")
            except Exception as notification_error:
                # Don't fail the status update if notifications fail
                print(f"⚠️ Failed to send notifications: {notification_error}")

        return {
            "success": True,
            "message": f"Task '{task.name}' status updated to {status_data.status}",
            "task_id": task_id,
            "new_status": status_data.status,
            "updated_at": now.isoformat(),
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ Error updating task status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update task status: {str(e)}"
        )


@router.get("/{task_id}")
async def get_task_details(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Get task details by ID - simple endpoint for task board/list functionality
    """
    try:  # Use raw SQL with more explicit typing to avoid SQLAlchemy issues
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
                p.name as project_name,
                u.id as assignee_id,
                u.name as assignee_username,
                u.email as assignee_email,
                up.first_name as assignee_first_name,
                up.last_name as assignee_last_name,
                up.display_name as assignee_display_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            LEFT JOIN users u ON ta.user_id = u.id
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE t.id = :task_id
        """
        )
        result = await db.execute(task_query, {"task_id": task_id})
        task_row = result.mappings().fetchone()

        if not task_row:
            raise HTTPException(
                status_code=404, detail="Task not found"
            )  # Extract data from the row result using dictionary-like access
        assignee_name = None
        assignee_initials = "?"

        if task_row["assignee_id"]:
            if task_row["assignee_display_name"]:
                assignee_name = task_row["assignee_display_name"]
            elif task_row["assignee_first_name"] or task_row["assignee_last_name"]:
                assignee_name = f"{task_row['assignee_first_name'] or ''} {task_row['assignee_last_name'] or ''}".strip()
            else:
                assignee_name = (
                    task_row["assignee_username"] or task_row["assignee_email"]
                )

            # Generate initials
            if task_row["assignee_first_name"] and task_row["assignee_last_name"]:
                assignee_initials = f"{task_row['assignee_first_name'][0]}{task_row['assignee_last_name'][0]}".upper()
            elif assignee_name:
                words = assignee_name.split()
                if len(words) >= 2:
                    assignee_initials = f"{words[0][0]}{words[1][0]}".upper()
                else:
                    assignee_initials = words[0][0].upper() if words else "?"

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
            "assignee": {
                "id": task_row["assignee_id"],
                "name": assignee_name or "Unassigned",
                "initials": assignee_initials,
            },
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
async def create_task(
    task_data: SimpleTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Create a new task - simple endpoint for task creation
    """
    try:
        # Insert task into database using raw SQL
        insert_query = text(
            """
            INSERT INTO tasks (
                name, description, status, priority, due_date, 
                estimated_hours, project_id, created_at, updated_at
            ) VALUES (
                :name, :description, :status, :priority, :due_date,
                :estimated_hours, :project_id, :created_at, :updated_at
            ) RETURNING id
        """
        )

        # Prepare the data
        current_time = datetime.now()
        query_params = {
            "name": task_data.title or task_data.name,
            "description": task_data.description,
            "status": task_data.status,
            "priority": task_data.priority,
            "due_date": (
                datetime.fromisoformat(task_data.due_date)
                if task_data.due_date
                else None
            ),
            "estimated_hours": task_data.estimated_hours,
            "project_id": task_data.project_id,
            "created_at": current_time,
            "updated_at": current_time,
        }

        result = await db.execute(insert_query, query_params)
        task_id = result.scalar()

        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to create task")

        # If there's an assignee, add to task_assignees table
        if task_data.assigned_to_id:
            assignee_query = text(
                """
                INSERT INTO task_assignees (task_id, user_id, assigned_at)
                VALUES (:task_id, :user_id, :assigned_at)
            """
            )
            await db.execute(
                assignee_query,
                {
                    "task_id": task_id,
                    "user_id": task_data.assigned_to_id,
                    "assigned_at": current_time,
                },
            )

        await db.commit()

        return {
            "id": task_id,
            "message": "Task created successfully",
            "title": task_data.title or task_data.name,
            "status": task_data.status,
            "project_id": task_data.project_id,
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.put("/{task_id}/assign")
async def update_task_assignment(
    task_id: int,
    assignment_data: TaskAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Update task assignment - assign or unassign a user to/from a task
    """
    try:
        # First, verify the task exists
        task_check_query = text("SELECT id FROM tasks WHERE id = :task_id")
        result = await db.execute(task_check_query, {"task_id": task_id})
        task_exists = result.scalar()

        if not task_exists:
            raise HTTPException(status_code=404, detail="Task not found")

        # If there's a new assignee, verify the user exists
        if assignment_data.assignee_id:
            user_check_query = text("SELECT id FROM users WHERE id = :user_id")
            result = await db.execute(
                user_check_query, {"user_id": assignment_data.assignee_id}
            )
            user_exists = result.scalar()

            if not user_exists:
                raise HTTPException(status_code=404, detail="User not found")

        # Remove existing assignment
        delete_assignment_query = text(
            "DELETE FROM task_assignees WHERE task_id = :task_id"
        )
        await db.execute(
            delete_assignment_query, {"task_id": task_id}
        )  # Add new assignment if provided
        if assignment_data.assignee_id:
            insert_assignment_query = text(
                """
                INSERT INTO task_assignees (task_id, user_id, assigned_at)
                VALUES (:task_id, :user_id, :assigned_at)
                """
            )
            await db.execute(
                insert_assignment_query,
                {
                    "task_id": task_id,
                    "user_id": assignment_data.assignee_id,
                    "assigned_at": datetime.now(),
                },
            )

        await db.commit()

        # Return updated task details
        return await get_task_details(task_id, db)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error updating task assignment: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update assignment: {str(e)}"
        )


@router.get("/{task_id}/comments")
async def get_task_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Get all comments for a specific task
    """
    try:
        # First, verify the task exists
        task_check_query = text("SELECT id FROM tasks WHERE id = :task_id")
        result = await db.execute(task_check_query, {"task_id": task_id})
        task_exists = result.scalar()

        if not task_exists:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get comments with user information
        comments_query = text(
            """
            SELECT 
                c.id,
                c.content,
                c.created_at,
                c.user_id,
                c.task_id,
                u.name as user_name,
                u.email as user_email
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.task_id = :task_id
            ORDER BY c.created_at ASC
        """
        )

        result = await db.execute(comments_query, {"task_id": task_id})
        comments_data = result.fetchall()

        # Format comments
        comments = []
        for comment in comments_data:
            comments.append(
                {
                    "id": comment.id,
                    "content": comment.content,
                    "created_at": comment.created_at,
                    "user_id": comment.user_id,
                    "task_id": comment.task_id,
                    "user": {
                        "id": comment.user_id,
                        "name": comment.user_name or "Unknown User",
                        "email": comment.user_email or "",
                    },
                }
            )

        return comments

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching task comments: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch comments: {str(e)}"
        )


@router.post("/{task_id}/comments")
async def add_task_comment(
    task_id: int,
    comment_data: TaskCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Add a new comment to a task
    """
    try:
        # First, verify the task exists
        task_check_query = text("SELECT id FROM tasks WHERE id = :task_id")
        result = await db.execute(task_check_query, {"task_id": task_id})
        task_exists = result.scalar()

        if not task_exists:
            raise HTTPException(status_code=404, detail="Task not found")

        # Use current_user instead of verifying user_id from request
        user_id = current_user.id

        # Insert the comment
        insert_comment_query = text(
            """
            INSERT INTO comments (content, user_id, task_id, created_at, updated_at)
            VALUES (:content, :user_id, :task_id, :created_at, :updated_at)
            RETURNING id, content, created_at, user_id, task_id
        """
        )

        now = datetime.now()
        result = await db.execute(
            insert_comment_query,
            {
                "content": comment_data.content,
                "user_id": user_id,
                "task_id": task_id,
                "created_at": now,
                "updated_at": now,
            },
        )

        comment_row = result.fetchone()
        await db.commit()  # Get user information for the response
        user_query = text("SELECT name, email FROM users WHERE id = :user_id")
        user_result = await db.execute(user_query, {"user_id": user_id})
        user_info = user_result.fetchone()

        # Return the created comment with user info
        return {
            "id": comment_row.id,
            "content": comment_row.content,
            "created_at": comment_row.created_at,
            "user_id": comment_row.user_id,
            "task_id": comment_row.task_id,
            "user": {
                "id": user_id,
                "name": user_info.name if user_info else current_user.name,
                "email": (
                    user_info.email if user_info else getattr(current_user, "email", "")
                ),
            },
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error adding task comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")


@router.get("/{task_id}/attachments")
async def get_task_attachments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Get all attachments for a specific task
    """
    try:
        # First, verify the task exists
        task_check_query = text("SELECT id FROM tasks WHERE id = :task_id")
        result = await db.execute(task_check_query, {"task_id": task_id})
        task_exists = result.scalar()

        if not task_exists:
            raise HTTPException(
                status_code=404, detail="Task not found"
            )  # Get attachments with user information - Updated for actual database structure
        try:
            attachments_query = text(
                """
                SELECT 
                    a.id,
                    a.file_name as filename,
                    a.file_size,
                    a.file_path,
                    a.created_at,
                    a.uploader_id as user_id,
                    ta.task_id,
                    u.name as user_name,
                    u.email as user_email
                FROM attachments a
                INNER JOIN task_attachments ta ON a.id = ta.attachment_id
                LEFT JOIN users u ON a.uploader_id = u.id
                WHERE ta.task_id = :task_id
                ORDER BY a.created_at DESC
            """
            )

            result = await db.execute(attachments_query, {"task_id": task_id})
            attachments_data = result.fetchall()
            print(
                f"DEBUG: Found {len(attachments_data)} attachments for task {task_id}"
            )

        except Exception as query_error:
            print(f"DEBUG: SQL Query error: {str(query_error)}")
            # Try a simpler query to check if the table structure is different
            try:
                simple_query = text("SELECT * FROM attachments LIMIT 1")
                result = await db.execute(simple_query)
                sample_row = result.fetchone()
                if sample_row:
                    print(f"DEBUG: Sample row columns: {sample_row._fields}")
                else:
                    print(f"DEBUG: No attachments found in table")
                # Return empty list if table exists but has structure issues
                return []
            except Exception as simple_error:
                print(f"DEBUG: Even simple query failed: {str(simple_error)}")
                raise query_error

        # Format attachments
        attachments = []
        for attachment in attachments_data:
            attachments.append(
                {
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "file_size": attachment.file_size,
                    "file_path": attachment.file_path,
                    "created_at": attachment.created_at,
                    "user_id": attachment.user_id,
                    "task_id": attachment.task_id,
                    "user": {
                        "id": attachment.user_id,
                        "name": attachment.user_name or "Unknown User",
                        "email": attachment.user_email or "",
                    },
                }
            )

        return attachments

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"Error fetching task attachments: {str(e)}")
        print(f"Full traceback: {error_details}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch attachments: {str(e)}"
        )


@router.post("/{task_id}/attachments")
async def upload_task_attachments(
    task_id: int,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Upload attachments to a task
    """
    import os
    import uuid
    from pathlib import Path

    try:
        # First, verify the task exists
        task_check_query = text("SELECT id FROM tasks WHERE id = :task_id")
        result = await db.execute(task_check_query, {"task_id": task_id})
        task_exists = result.scalar()

        if not task_exists:
            raise HTTPException(status_code=404, detail="Task not found")

        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/tasks")
        upload_dir.mkdir(parents=True, exist_ok=True)

        uploaded_attachments = []

        for file in files:
            # Validate file size (10MB max)
            if file.size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} is too large. Maximum size is 10MB.",
                )

            # Generate unique filename
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename

            # Save file to disk
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(
                    content
                )  # Insert attachment record (using actual model structure)
            insert_attachment_query = text(
                """
                INSERT INTO attachments (file_name, file_size, file_path, uploader_id, created_at, updated_at)
                VALUES (:file_name, :file_size, :file_path, :uploader_id, :created_at, :updated_at)
                RETURNING id, file_name, file_size, file_path, created_at, uploader_id
            """
            )

            now = datetime.now()
            result = await db.execute(
                insert_attachment_query,
                {
                    "file_name": file.filename,
                    "file_size": file.size,
                    "file_path": str(file_path),
                    "uploader_id": current_user.id,
                    "created_at": now,
                    "updated_at": now,
                },
            )

            attachment_row = result.fetchone()

            # Link attachment to task using association table
            link_task_attachment_query = text(
                """
                INSERT INTO task_attachments (task_id, attachment_id, attached_at)
                VALUES (:task_id, :attachment_id, :attached_at)
            """
            )
            await db.execute(
                link_task_attachment_query,
                {
                    "task_id": task_id,
                    "attachment_id": attachment_row.id,
                    "attached_at": now,
                },
            )

            uploaded_attachments.append(
                {
                    "id": attachment_row.id,
                    "filename": attachment_row.file_name,  # Using actual column name
                    "file_size": attachment_row.file_size,
                    "file_path": attachment_row.file_path,
                    "created_at": attachment_row.created_at,
                    "user_id": attachment_row.uploader_id,  # Using actual column name
                    "task_id": task_id,  # From parameter since it's not in attachment table
                    "user": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "email": getattr(current_user, "email", ""),
                    },
                }
            )

        await db.commit()
        return {
            "message": f"{len(uploaded_attachments)} file(s) uploaded successfully",
            "attachments": uploaded_attachments,
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error uploading task attachments: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload attachments: {str(e)}"
        )


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Download a task attachment
    """
    try:  # Get attachment info (using actual column names)
        attachment_query = text(
            """
            SELECT file_name as filename, file_path, file_size
            FROM attachments 
            WHERE id = :attachment_id
        """
        )

        result = await db.execute(attachment_query, {"attachment_id": attachment_id})
        attachment = result.fetchone()

        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")

        # Check if file exists
        file_path = Path(attachment.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=str(file_path),
            filename=attachment.filename,
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading attachment: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to download attachment: {str(e)}"
        )


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_web),
):
    """
    Delete a task attachment
    """
    try:  # Get attachment info (using actual column names)
        attachment_query = text(
            """
            SELECT file_name as filename, file_path, uploader_id as user_id
            FROM attachments 
            WHERE id = :attachment_id
        """
        )

        result = await db.execute(attachment_query, {"attachment_id": attachment_id})
        attachment = result.fetchone()

        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")

        # Check if user owns the attachment or has appropriate permissions
        # For now, allow any authenticated user to delete attachments
        # You can add more restrictive permissions here if needed        # Delete file from disk
        file_path = Path(attachment.file_path)
        if file_path.exists():
            file_path.unlink()

        # Delete from association table first (due to foreign key constraints)
        delete_association_query = text(
            "DELETE FROM task_attachments WHERE attachment_id = :attachment_id"
        )
        await db.execute(delete_association_query, {"attachment_id": attachment_id})

        # Delete attachment record
        delete_query = text("DELETE FROM attachments WHERE id = :attachment_id")
        await db.execute(delete_query, {"attachment_id": attachment_id})
        await db.commit()

        return {"message": f"Attachment '{attachment.filename}' deleted successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        print(f"Error deleting attachment: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete attachment: {str(e)}"
        )

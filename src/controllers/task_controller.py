from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from fastapi import HTTPException, status

from src.models_backup.marketing_project import (
    MarketingProject, WorkflowStep, MarketingTask, 
    TaskStatus, TaskPriority, TaskComment
)
from src.schemas.marketing_project import (
    WorkflowStepCreate, WorkflowStepUpdate, WorkflowStepRead,
    MarketingTaskCreate, MarketingTaskUpdate, MarketingTaskRead, MarketingTaskReadBasic,
    TaskCommentCreate, TaskCommentRead
)

# Configure logging
logger = logging.getLogger(__name__)


class TaskController:
    """Controller for handling tasks and workflow operations"""
    
    # ==================== Workflow Step Methods ====================
    @staticmethod
    async def get_workflow_steps(project_id: int, db: AsyncSession) -> List[WorkflowStep]:
        """
        Get all workflow steps for a project
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # Get workflow steps with eager loading of assignee
            query = select(WorkflowStep).filter(
                WorkflowStep.project_id == project_id
            ).options(
                joinedload(WorkflowStep.assigned_to)
            ).order_by(WorkflowStep.step_number)
            
            result = await db.execute(query)
            steps = result.scalars().unique().all()
            
            return steps
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching workflow steps for project {project_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch workflow steps: {str(e)}"
            )
    
    @staticmethod
    async def get_workflow_step(
        project_id: int, 
        step_id: int, 
        db: AsyncSession
    ) -> WorkflowStep:
        """
        Get a specific workflow step
        """
        try:
            # Get the step with eager loading
            query = select(WorkflowStep).filter(
                WorkflowStep.project_id == project_id,
                WorkflowStep.id == step_id
            ).options(
                joinedload(WorkflowStep.assigned_to)
            )
            
            result = await db.execute(query)
            step = result.scalars().unique().first()
            
            if not step:
                logger.warning(f"Workflow step with ID {step_id} not found for project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workflow step with ID {step_id} not found for project {project_id}"
                )
            
            return step
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching workflow step {step_id} for project {project_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch workflow step: {str(e)}"
            )
    
    @staticmethod
    async def update_workflow_step(
        project_id: int,
        step_id: int,
        step_data: WorkflowStepUpdate,
        db: AsyncSession
    ) -> WorkflowStep:
        """
        Update a workflow step
        """
        try:
            # Get the step
            step = await TaskController.get_workflow_step(project_id, step_id, db)
            
            # Update step attributes
            update_data = step_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(step, key, value)
            
            await db.commit()
            await db.refresh(step)
            
            logger.info(f"Updated workflow step {step_id} for project {project_id}")
            
            # Return the updated step with full details
            return await TaskController.get_workflow_step(project_id, step_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating workflow step {step_id} for project {project_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update workflow step: {str(e)}"
            )
    
    # ==================== Task Methods ====================
    @staticmethod
    async def create_task(
        project_id: int,
        task_data: MarketingTaskCreate,
        db: AsyncSession
    ) -> MarketingTask:
        """
        Create a new task for a project
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # If workflow step ID provided, verify it belongs to the project
            if task_data.workflow_step_id:
                step_query = select(WorkflowStep).filter(
                    WorkflowStep.id == task_data.workflow_step_id,
                    WorkflowStep.project_id == project_id
                )
                step_result = await db.execute(step_query)
                step = step_result.scalars().first()
                
                if not step:
                    logger.warning(f"Workflow step with ID {task_data.workflow_step_id} not found for project {project_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Workflow step with ID {task_data.workflow_step_id} not found for project {project_id}"
                    )
            
            # If parent task ID provided, verify it belongs to the project
            if task_data.parent_task_id:
                parent_query = select(MarketingTask).filter(
                    MarketingTask.id == task_data.parent_task_id,
                    MarketingTask.project_id == project_id
                )
                parent_result = await db.execute(parent_query)
                parent = parent_result.scalars().first()
                
                if not parent:
                    logger.warning(f"Parent task with ID {task_data.parent_task_id} not found for project {project_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Parent task with ID {task_data.parent_task_id} not found for project {project_id}"
                    )
            
            # Create the task
            new_task = MarketingTask(
                project_id=project_id,
                workflow_step_id=task_data.workflow_step_id,
                title=task_data.title,
                description=task_data.description,
                task_type=task_data.task_type,
                status=task_data.status,
                priority=task_data.priority,
                due_date=task_data.due_date,
                start_date=task_data.start_date,
                completed_date=task_data.completed_date,
                creator_id=task_data.creator_id,
                assignee_id=task_data.assignee_id,
                parent_task_id=task_data.parent_task_id,
                estimated_hours=task_data.estimated_hours,
                actual_hours=task_data.actual_hours,
                completion_percentage=task_data.completion_percentage
            )
            
            db.add(new_task)
            await db.commit()
            await db.refresh(new_task)
            
            logger.info(f"Created new task: {new_task.title} for project {project_id}")
            
            # Return the created task with related info
            return await TaskController.get_task(new_task.id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating task for project {project_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {str(e)}"
            )
    
    @staticmethod
    async def get_project_tasks(
        project_id: int,
        workflow_step_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
        parent_task_id: Optional[int] = None,
        search: Optional[str] = None,
        include_subtasks: bool = True,
        db: AsyncSession = None
    ) -> List[MarketingTask]:
        """
        Get tasks for a project with optional filtering
        """
        try:
            # Verify project exists
            project_query = select(MarketingProject).filter(MarketingProject.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalars().first()
            
            if not project:
                logger.warning(f"Project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            # Build query with filters
            query = select(MarketingTask).filter(MarketingTask.project_id == project_id)
            
            # Only get top-level tasks unless parent_task_id is specified
            if not parent_task_id and not include_subtasks:
                query = query.filter(MarketingTask.parent_task_id == None)
            elif parent_task_id:
                query = query.filter(MarketingTask.parent_task_id == parent_task_id)
            
            if workflow_step_id:
                query = query.filter(MarketingTask.workflow_step_id == workflow_step_id)
            if status:
                query = query.filter(MarketingTask.status == status)
            if priority:
                query = query.filter(MarketingTask.priority == priority)
            if assignee_id:
                query = query.filter(MarketingTask.assignee_id == assignee_id)
            if search:
                query = query.filter(MarketingTask.title.ilike(f"%{search}%"))
            
            # Add eager loading
            query = query.options(
                joinedload(MarketingTask.creator),
                joinedload(MarketingTask.assignee),
                joinedload(MarketingTask.workflow_step)
            )
            
            # Execute query
            result = await db.execute(query)
            tasks = result.scalars().unique().all()
            
            return tasks
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching tasks for project {project_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch tasks: {str(e)}"
            )
    
    @staticmethod
    async def get_task(task_id: int, db: AsyncSession) -> MarketingTask:
        """
        Get a specific task by ID
        """
        try:
            # Query with eager loading
            query = select(MarketingTask).filter(
                MarketingTask.id == task_id
            ).options(
                joinedload(MarketingTask.creator),
                joinedload(MarketingTask.assignee),
                joinedload(MarketingTask.workflow_step),
                joinedload(MarketingTask.project),
                joinedload(MarketingTask.comments).joinedload(TaskComment.user),
                joinedload(MarketingTask.subtasks).joinedload(MarketingTask.assignee)
            )
            
            result = await db.execute(query)
            task = result.scalars().unique().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            return task
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch task: {str(e)}"
            )
    
    @staticmethod
    async def update_task(task_id: int, task_data: MarketingTaskUpdate, db: AsyncSession) -> MarketingTask:
        """
        Update a task
        """
        try:
            # Get the task
            query = select(MarketingTask).filter(MarketingTask.id == task_id)
            result = await db.execute(query)
            task = result.scalars().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            # Update task attributes
            update_data = task_data.dict(exclude_unset=True)
            
            # Special handling for status changes
            if "status" in update_data and update_data["status"] != task.status:
                # If changing to COMPLETED, set completed_date to now if not provided
                if update_data["status"] == TaskStatus.COMPLETED and not update_data.get("completed_date"):
                    update_data["completed_date"] = datetime.now()
                    # Also set completion percentage to 100% if not provided
                    if not update_data.get("completion_percentage"):
                        update_data["completion_percentage"] = 100
                
                # If changing from COMPLETED to something else, clear completed_date
                elif task.status == TaskStatus.COMPLETED and update_data["status"] != TaskStatus.COMPLETED:
                    update_data["completed_date"] = None
            
            # If workflow_step_id is provided, verify it belongs to the project
            if "workflow_step_id" in update_data and update_data["workflow_step_id"]:
                step_query = select(WorkflowStep).filter(
                    WorkflowStep.id == update_data["workflow_step_id"],
                    WorkflowStep.project_id == task.project_id
                )
                step_result = await db.execute(step_query)
                step = step_result.scalars().first()
                
                if not step:
                    logger.warning(f"Workflow step with ID {update_data['workflow_step_id']} not found for project {task.project_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Workflow step with ID {update_data['workflow_step_id']} not found for project {task.project_id}"
                    )
            
            for key, value in update_data.items():
                setattr(task, key, value)
            
            await db.commit()
            await db.refresh(task)
            
            logger.info(f"Updated task {task_id}: {task.title}")
            
            # Return the updated task with full details
            return await TaskController.get_task(task_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update task: {str(e)}"
            )
    
    @staticmethod
    async def delete_task(task_id: int, db: AsyncSession) -> None:
        """
        Delete a task
        """
        try:
            # Get the task
            query = select(MarketingTask).filter(MarketingTask.id == task_id)
            result = await db.execute(query)
            task = result.scalars().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            # Delete the task
            await db.delete(task)
            await db.commit()
            
            logger.info(f"Deleted task {task_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete task: {str(e)}"
            )
    
    # ==================== Task Comment Methods ====================
    @staticmethod
    async def create_task_comment(
        task_id: int,
        comment_data: TaskCommentCreate,
        db: AsyncSession
    ) -> TaskComment:
        """
        Add a comment to a task
        """
        try:
            # Verify task exists
            task_query = select(MarketingTask).filter(MarketingTask.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalars().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            # Create comment
            new_comment = TaskComment(
                task_id=task_id,
                user_id=comment_data.user_id,
                content=comment_data.content
            )
            
            db.add(new_comment)
            await db.commit()
            await db.refresh(new_comment)
            
            logger.info(f"Added comment to task {task_id}")
            
            # Return comment with user info
            comment_query = select(TaskComment).filter(
                TaskComment.id == new_comment.id
            ).options(
                joinedload(TaskComment.user)
            )
            
            result = await db.execute(comment_query)
            comment = result.scalars().unique().first()
            
            return comment
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding comment to task {task_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add comment: {str(e)}"
            )
    
    @staticmethod
    async def get_task_comments(task_id: int, db: AsyncSession) -> List[TaskComment]:
        """
        Get all comments for a task
        """
        try:
            # Verify task exists
            task_query = select(MarketingTask).filter(MarketingTask.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalars().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            # Get comments with user info
            query = select(TaskComment).filter(
                TaskComment.task_id == task_id
            ).options(
                joinedload(TaskComment.user)
            ).order_by(TaskComment.created_at)
            
            result = await db.execute(query)
            comments = result.scalars().unique().all()
            
            return comments
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching comments for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch comments: {str(e)}"
            )
    
    @staticmethod
    async def update_task_comment(
        task_id: int,
        comment_id: int,
        comment_data: TaskCommentCreate,  # Reusing TaskCommentCreate schema
        db: AsyncSession
    ) -> TaskComment:
        """
        Update a task comment
        """
        try:
            # Verify task exists
            task_query = select(MarketingTask).filter(MarketingTask.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalars().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            # Get the comment
            comment_query = select(TaskComment).filter(
                TaskComment.id == comment_id,
                TaskComment.task_id == task_id
            )
            
            comment_result = await db.execute(comment_query)
            comment = comment_result.scalars().first()
            
            if not comment:
                logger.warning(f"Comment with ID {comment_id} not found for task {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comment with ID {comment_id} not found for task {task_id}"
                )
            
            # Verify user is the creator of the comment
            if comment_data.user_id != comment.user_id:
                logger.warning(f"User {comment_data.user_id} not authorized to update comment {comment_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to update this comment"
                )
            
            # Update comment content
            comment.content = comment_data.content
            
            await db.commit()
            await db.refresh(comment)
            
            logger.info(f"Updated comment {comment_id} for task {task_id}")
            
            # Return comment with user info
            comment_query = select(TaskComment).filter(
                TaskComment.id == comment.id
            ).options(
                joinedload(TaskComment.user)
            )
            
            result = await db.execute(comment_query)
            updated_comment = result.scalars().unique().first()
            
            return updated_comment
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating comment {comment_id} for task {task_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update comment: {str(e)}"
            )
    
    @staticmethod
    async def delete_task_comment(task_id: int, comment_id: int, user_id: int, db: AsyncSession) -> None:
        """
        Delete a task comment
        """
        try:
            # Verify task exists
            task_query = select(MarketingTask).filter(MarketingTask.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalars().first()
            
            if not task:
                logger.warning(f"Task with ID {task_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found"
                )
            
            # Get the comment
            comment_query = select(TaskComment).filter(
                TaskComment.id == comment_id,
                TaskComment.task_id == task_id
            )
            
            comment_result = await db.execute(comment_query)
            comment = comment_result.scalars().first()
            
            if not comment:
                logger.warning(f"Comment with ID {comment_id} not found for task {task_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comment with ID {comment_id} not found for task {task_id}"
                )
            
            # Verify user is the creator of the comment
            if user_id != comment.user_id:
                logger.warning(f"User {user_id} not authorized to delete comment {comment_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to delete this comment"
                )
            
            # Delete the comment
            await db.delete(comment)
            await db.commit()
            
            logger.info(f"Deleted comment {comment_id} from task {task_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id} from task {task_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete comment: {str(e)}"
            )

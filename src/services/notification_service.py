"""
Notification Service - Handles creation and sending of notifications
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.models.notification import Notification, NotificationTypeEnum
from src.models.user import User
from src.models.task import Task
from src.models.project import Project

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing notifications"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationTypeEnum,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Notification:
        """
        Create a new notification for a user

        Args:
            db: Database session
            user_id: ID of the user to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            task_id: Optional task ID for task-related notifications
            project_id: Optional project ID for project-related notifications

        Returns:
            Created notification object
        """
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                task_id=task_id,
                project_id=project_id,
            )

            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            logger.info(f"Created notification for user {user_id}: {title}")
            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def notify_task_status_change(
        db: AsyncSession,
        task_id: int,
        old_status: str,
        new_status: str,
        updated_by_id: int,
    ):
        """
        Notify project members when a task status changes

        Args:
            db: Database session
            task_id: ID of the updated task
            old_status: Previous task status
            new_status: New task status
            updated_by_id: ID of user who made the change
        """
        try:
            # Get task with project and assignee info
            task_query = select(Task).where(Task.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task {task_id} not found for notification")
                return

            # Get project details
            project_query = select(Project).where(Project.id == task.project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()

            if not project:
                logger.warning(f"Project {task.project_id} not found for notification")
                return

            # Get the user who made the change
            updater_query = select(User).where(User.id == updated_by_id)
            updater_result = await db.execute(updater_query)
            updater = updater_result.scalar_one_or_none()
            updater_name = updater.name if updater else "Someone"

            # Create notification message
            title = f"Task Status Updated: {task.title}"
            message = f"{updater_name} changed task '{task.title}' status from '{old_status}' to '{new_status}' in project '{project.name}'"

            # Get all project team members (including owner and assignee)
            members_to_notify = set()

            # Add project owner
            members_to_notify.add(project.owner_id)

            # Add task assignee if exists
            if task.assigned_to:
                members_to_notify.add(task.assigned_to)

            # Add project team members if they exist
            if hasattr(project, "team_members") and project.team_members:
                for member in project.team_members:
                    members_to_notify.add(member.id)

            # Remove the person who made the change (don't notify themselves)
            members_to_notify.discard(updated_by_id)

            # Create notifications for all relevant users
            for user_id in members_to_notify:
                await NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=(
                        NotificationTypeEnum.TASK_COMPLETED
                        if new_status.lower() == "completed"
                        else NotificationTypeEnum.PROJECT_UPDATE
                    ),
                    task_id=task_id,
                    project_id=project.id,
                )

            logger.info(
                f"Sent task status change notifications to {len(members_to_notify)} users"
            )

        except Exception as e:
            logger.error(f"Error sending task status change notifications: {e}")

    @staticmethod
    async def notify_task_assignment(
        db: AsyncSession,
        task_id: int,
        assigned_to_id: int,
        assigned_by_id: int,
    ):
        """
        Notify when a task is assigned to someone

        Args:
            db: Database session
            task_id: ID of the assigned task
            assigned_to_id: ID of user task was assigned to
            assigned_by_id: ID of user who made the assignment
        """
        try:
            # Get task and project info
            task_query = select(Task).where(Task.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalar_one_or_none()

            if not task:
                return

            project_query = select(Project).where(Project.id == task.project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()

            # Get assigner name
            assigner_query = select(User).where(User.id == assigned_by_id)
            assigner_result = await db.execute(assigner_query)
            assigner = assigner_result.scalar_one_or_none()
            assigner_name = assigner.name if assigner else "Someone"

            # Notify the assigned user
            title = f"New Task Assigned: {task.title}"
            message = f"{assigner_name} assigned you the task '{task.title}' in project '{project.name if project else 'Unknown'}'"

            await NotificationService.create_notification(
                db=db,
                user_id=assigned_to_id,
                title=title,
                message=message,
                notification_type=NotificationTypeEnum.TASK_ASSIGNED,
                task_id=task_id,
                project_id=task.project_id,
            )

            logger.info(f"Sent task assignment notification to user {assigned_to_id}")

        except Exception as e:
            logger.error(f"Error sending task assignment notification: {e}")

    @staticmethod
    async def notify_project_update(
        db: AsyncSession,
        project_id: int,
        title: str,
        message: str,
        updated_by_id: int,
    ):
        """
        Notify project members of project updates

        Args:
            db: Database session
            project_id: ID of the updated project
            title: Notification title
            message: Notification message
            updated_by_id: ID of user who made the update
        """
        try:
            # Get project details
            project_query = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()

            if not project:
                return

            # Get all project team members
            members_to_notify = set()

            # Add project owner
            members_to_notify.add(project.owner_id)

            # Add project team members if they exist
            if hasattr(project, "team_members") and project.team_members:
                for member in project.team_members:
                    members_to_notify.add(member.id)

            # Remove the person who made the change
            members_to_notify.discard(updated_by_id)

            # Create notifications for all relevant users
            for user_id in members_to_notify:
                await NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=NotificationTypeEnum.PROJECT_UPDATE,
                    project_id=project_id,
                )

            logger.info(
                f"Sent project update notifications to {len(members_to_notify)} users"
            )

        except Exception as e:
            logger.error(f"Error sending project update notifications: {e}")

    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """
        Get notifications for a user

        Args:
            db: Database session
            user_id: ID of the user
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return

        Returns:
            List of notifications
        """
        try:
            query = select(Notification).where(Notification.user_id == user_id)

            if unread_only:
                query = query.where(Notification.is_read == False)

            query = query.order_by(Notification.created_at.desc()).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    @staticmethod
    async def mark_notification_read(
        db: AsyncSession,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """
        Mark a notification as read

        Args:
            db: Database session
            notification_id: ID of the notification
            user_id: ID of the user (for security)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            result = await db.execute(query)
            notification = result.scalar_one_or_none()

            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                await db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            await db.rollback()
            return False

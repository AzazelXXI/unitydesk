"""
WebSocket Notification Manager - Real-time notifications using Socket.IO
"""

import logging
from typing import Dict, Set, List, Optional
from datetime import datetime
import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.user import User
from src.models.project import Project
from src.models.task import Task
from src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and real-time notifications"""

    def __init__(self):
        # Store active connections: {user_id: websocket}
        self.active_connections: Dict[int, WebSocket] = {}

        # Store user project subscriptions: {user_id: {project_ids}}
        self.user_project_subscriptions: Dict[int, Set[int]] = {}

        # Store project members: {project_id: {user_ids}}
        self.project_members: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection and add to active connections"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to WebSocket")

    def disconnect(self, user_id: int):
        """Remove user from active connections and subscriptions"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

        if user_id in self.user_project_subscriptions:
            # Remove user from all project member lists
            for project_id in self.user_project_subscriptions[user_id]:
                if project_id in self.project_members:
                    self.project_members[project_id].discard(user_id)
            del self.user_project_subscriptions[user_id]

        logger.info(f"User {user_id} disconnected from WebSocket")

    async def subscribe_to_projects(
        self, user_id: int, project_ids: List[int], db: AsyncSession
    ):
        """Subscribe user to project notifications"""
        if user_id not in self.user_project_subscriptions:
            self.user_project_subscriptions[user_id] = set()

        for project_id in project_ids:
            # Add to user's subscriptions
            self.user_project_subscriptions[user_id].add(project_id)

            # Add to project members
            if project_id not in self.project_members:
                self.project_members[project_id] = set()
            self.project_members[project_id].add(user_id)

        logger.info(f"User {user_id} subscribed to projects: {project_ids}")

    async def send_personal_message(self, user_id: int, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id)

    async def broadcast_to_project(
        self, project_id: int, message: dict, exclude_user_id: Optional[int] = None
    ):
        """Send message to all members of a project"""
        if project_id not in self.project_members:
            logger.warning(f"No members found for project {project_id}")
            return

        recipients = self.project_members[project_id].copy()
        if exclude_user_id:
            recipients.discard(exclude_user_id)

        # Send to all connected project members
        failed_connections = []
        for user_id in recipients:
            if user_id in self.active_connections:
                try:
                    websocket = self.active_connections[user_id]
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    failed_connections.append(user_id)

        # Clean up failed connections
        for user_id in failed_connections:
            self.disconnect(user_id)

        logger.info(
            f"Broadcasted message to {len(recipients)} members of project {project_id}"
        )

    async def notify_task_status_change(
        self,
        db: AsyncSession,
        task_id: int,
        old_status: str,
        new_status: str,
        updated_by_user_id: int,
    ):
        """Send real-time notification when task status changes"""
        try:
            # Get task details
            task_query = select(Task).where(Task.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task {task_id} not found")
                return

            # Get project details
            project_query = select(Project).where(Project.id == task.project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()

            # Get user who made the change
            user_query = select(User).where(User.id == updated_by_user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            user_name = user.name if user else "Someone"
            project_name = project.name if project else "Unknown Project"

            # Create WebSocket message
            message = {
                "type": "task_status_update",
                "data": {
                    "task_id": task_id,
                    "task_title": task.name,
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_by": user_name,
                    "updated_by_id": updated_by_user_id,
                    "project_id": task.project_id,
                    "project_name": project_name,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"{user_name} changed task '{task.name}' from '{old_status}' to '{new_status}' in {project_name}",
                },
            }

            # Send to all project members via WebSocket
            await self.broadcast_to_project(
                project_id=task.project_id,
                message=message,
                exclude_user_id=updated_by_user_id,  # Don't notify the person who made the change
            )

            # Also create database notification
            await NotificationService.notify_task_status_change(
                db=db,
                task_id=task_id,
                old_status=old_status,
                new_status=new_status,
                updated_by_id=updated_by_user_id,
            )

            logger.info(f"Sent real-time task status notification for task {task_id}")

        except Exception as e:
            logger.error(f"Error sending real-time task notification: {e}")

    async def notify_task_assignment(
        self,
        db: AsyncSession,
        task_id: int,
        assigned_to_user_id: int,
        assigned_by_user_id: int,
    ):
        """Send real-time notification when task is assigned"""
        try:
            # Get task and user details
            task_query = select(Task).where(Task.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalar_one_or_none()

            assigned_by_query = select(User).where(User.id == assigned_by_user_id)
            assigned_by_result = await db.execute(assigned_by_query)
            assigned_by_user = assigned_by_result.scalar_one_or_none()

            if not task or not assigned_by_user:
                return

            # Create WebSocket message
            message = {
                "type": "task_assignment",
                "data": {
                    "task_id": task_id,
                    "task_title": task.name,
                    "assigned_by": assigned_by_user.name,
                    "assigned_by_id": assigned_by_user_id,
                    "project_id": task.project_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"{assigned_by_user.name} assigned you the task '{task.name}'",
                },
            }

            # Send to assigned user
            await self.send_personal_message(assigned_to_user_id, message)

            # Also create database notification
            await NotificationService.notify_task_assignment(
                db=db,
                task_id=task_id,
                assigned_to_id=assigned_to_user_id,
                assigned_by_id=assigned_by_user_id,
            )

        except Exception as e:
            logger.error(f"Error sending task assignment notification: {e}")

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        return {
            "active_connections": len(self.active_connections),
            "subscribed_users": len(self.user_project_subscriptions),
            "projects_with_subscribers": len(self.project_members),
            "total_subscriptions": sum(
                len(projects) for projects in self.user_project_subscriptions.values()
            ),
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

"""
Activity Service - Handles project activity logging and retrieval
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Dict, Any, Optional
import logging

from src.models.activity import ProjectActivity, ActivityType
from src.models.user import User

logger = logging.getLogger(__name__)


class ActivityService:

    @staticmethod
    async def log_activity(
        db: AsyncSession,
        project_id: int,
        user_id: int,
        activity_type: ActivityType,
        description: str,
        target_entity_type: str = None,
        target_entity_id: int = None,
        metadata: dict = None,
    ) -> ProjectActivity:
        """Log a new activity for a project"""
        try:
            activity = ProjectActivity.create_activity(
                project_id=project_id,
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                target_entity_type=target_entity_type,
                target_entity_id=target_entity_id,
                metadata=metadata,
            )

            db.add(activity)
            await db.commit()
            await db.refresh(activity)

            logger.info(
                f"Activity logged: {activity_type.value} for project {project_id}"
            )
            return activity

        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def get_recent_activities(
        db: AsyncSession, project_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activities for a project"""
        try:
            query = text(
                """
                SELECT 
                    pa.id,
                    pa.activity_type,
                    pa.description,
                    pa.target_entity_type,
                    pa.target_entity_id,
                    pa.metadata,
                    pa.created_at,
                    u.id as user_id,
                    u.name as user_name,
                    u.email as user_email
                FROM project_activities pa
                JOIN users u ON pa.user_id = u.id
                WHERE pa.project_id = :project_id
                ORDER BY pa.created_at DESC
                LIMIT :limit
            """
            )

            result = await db.execute(query, {"project_id": project_id, "limit": limit})
            rows = result.fetchall()

            activities = []
            for row in rows:
                activity = {
                    "id": row.id,
                    "activity_type": row.activity_type,
                    "description": row.description,
                    "target_entity_type": row.target_entity_type,
                    "target_entity_id": row.target_entity_id,
                    "metadata": row.metadata,
                    "created_at": row.created_at,
                    "user": {
                        "id": row.user_id,
                        "name": row.user_name,
                        "email": row.user_email,
                    },
                    "icon": ProjectActivity.format_activity_icon(row.activity_type),
                    "color": ProjectActivity.format_activity_color(row.activity_type),
                }
                activities.append(activity)

            return activities

        except Exception as e:
            logger.error(f"Error fetching activities: {str(e)}")
            return []

    @staticmethod
    def create_task_activity_description(
        action: str, task_name: str, user_name: str, **kwargs
    ) -> str:
        """Create standardized descriptions for task activities"""
        templates = {
            "created": f'{user_name} created task "{task_name}"',
            "completed": f'{user_name} completed task "{task_name}"',
            "assigned": f"{user_name} assigned task \"{task_name}\" to {kwargs.get('assignee', 'someone')}",
            "status_changed": f"{user_name} changed status of \"{task_name}\" to {kwargs.get('new_status', 'unknown')}",
            "updated": f'{user_name} updated task "{task_name}"',
        }
        return templates.get(action, f'{user_name} {action} task "{task_name}"')

    @staticmethod
    def create_project_activity_description(
        action: str, project_name: str, user_name: str, **kwargs
    ) -> str:
        """Create standardized descriptions for project activities"""
        templates = {
            "created": f"{user_name} created the project",
            "updated": f"{user_name} updated project details",
            "status_changed": f"{user_name} changed project status to {kwargs.get('new_status', 'unknown')}",
        }
        return templates.get(action, f"{user_name} {action} the project")

    @staticmethod
    def create_member_activity_description(
        action: str, user_name: str, member_name: str
    ) -> str:
        """Create standardized descriptions for member activities"""
        templates = {
            "added": f"{user_name} added {member_name} to the project",
            "removed": f"{user_name} removed {member_name} from the project",
        }
        return templates.get(action, f"{user_name} {action} {member_name}")

    @staticmethod
    def create_file_activity_description(
        action: str, file_name: str, user_name: str
    ) -> str:
        """Create standardized descriptions for file activities"""
        templates = {
            "uploaded": f'{user_name} uploaded file "{file_name}"',
            "deleted": f'{user_name} deleted file "{file_name}"',
        }
        return templates.get(action, f'{user_name} {action} file "{file_name}"')

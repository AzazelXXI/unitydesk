"""
Project Status Service - Manages both default and project-specific custom statuses
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Dict, Optional
import logging

from src.models.custom_project_status import ProjectCustomStatus
from src.models.project import DEFAULT_PROJECT_STATUSES

logger = logging.getLogger(__name__)


class ProjectStatusService:
    """Service for managing project statuses (default + project-specific custom)"""

    @staticmethod
    async def get_project_statuses(
        db: AsyncSession, project_id: int
    ) -> List[Dict[str, str]]:
        """
        Get all available statuses for a specific project (default + custom)
        Returns list of dicts with status_name and display_name
        """
        try:
            statuses = []

            # Add default project statuses
            default_colors = {
                "Planning": "#6c757d",
                "In Progress": "#007bff",
                "Completed": "#28a745",
                "Canceled": "#dc3545",
            }

            for status in DEFAULT_PROJECT_STATUSES:
                statuses.append(
                    {
                        "status_name": status,
                        "display_name": status,
                        "is_custom": False,
                        "color": default_colors.get(status, "#6c757d"),
                        "description": f"Default {status} status",
                        "is_final": status in ["Completed", "Canceled"],
                        "id": None,
                        "project_id": project_id,
                    }
                )

            # Get custom statuses for this specific project
            query = select(ProjectCustomStatus).where(
                ProjectCustomStatus.project_id == project_id,
                ProjectCustomStatus.is_active == True,
            )

            result = await db.execute(query)
            custom_statuses = result.scalars().all()

            for custom_status in custom_statuses:
                statuses.append(
                    {
                        "status_name": custom_status.status_name,
                        "display_name": custom_status.display_name,
                        "is_custom": True,
                        "color": custom_status.color,
                        "description": custom_status.description
                        or f"Custom {custom_status.display_name} status",
                        "is_final": custom_status.is_final,
                        "id": custom_status.id,
                        "project_id": project_id,
                    }
                )

            # No sort_order: statuses are returned in the order they were added
            return statuses

        except Exception as e:
            logger.error(
                f"Error getting project statuses for project {project_id}: {str(e)}"
            )
            # Fallback to default statuses only
            return [
                {
                    "status_name": status,
                    "display_name": status,
                    "is_custom": False,
                    "color": "#6c757d",
                    "description": f"Default {status} status",
                    "is_final": status in ["Completed", "Canceled"],
                    "id": None,
                    "project_id": project_id,
                }
                for status in DEFAULT_PROJECT_STATUSES
            ]

    @staticmethod
    async def get_all_project_statuses(db: AsyncSession) -> List[Dict[str, str]]:
        """
        Get default statuses (for new project creation before project is created)
        This is for backward compatibility with existing code
        """
        default_colors = {
            "Planning": "#6c757d",
            "In Progress": "#007bff",
            "Completed": "#28a745",
            "Canceled": "#dc3545",
        }

        return [
            {
                "status_name": status,
                "display_name": status,
                "is_custom": False,
                "color": default_colors.get(status, "#6c757d"),
                "description": f"Default {status} status",
                "is_final": status in ["Completed", "Canceled"],
                "id": None,
            }
            for status in DEFAULT_PROJECT_STATUSES
        ]

    @staticmethod
    async def create_custom_project_status(
        db: AsyncSession,
        project_id: int,
        status_name: str,
        display_name: str,
        description: str = None,
        color: str = "#007bff",
        is_final: bool = False,
    ) -> ProjectCustomStatus:
        """Create a new custom status for a specific project"""
        try:
            # Check if status already exists for this project
            existing_query = select(ProjectCustomStatus).where(
                ProjectCustomStatus.project_id == project_id,
                ProjectCustomStatus.status_name == status_name.replace(" ", "_"),
            )
            existing = await db.execute(existing_query)
            if existing.scalar_one_or_none():
                raise ValueError(
                    f"Status '{status_name}' already exists for this project"
                )

            # Check if it conflicts with default statuses
            if status_name in DEFAULT_PROJECT_STATUSES:
                raise ValueError(
                    f"Status '{status_name}' conflicts with default statuses"
                )

            custom_status = ProjectCustomStatus(
                project_id=project_id,
                status_name=status_name,
                display_name=display_name,
                description=description,
                color=color,
                is_final=is_final,
            )

            db.add(custom_status)
            await db.commit()
            await db.refresh(custom_status)

            logger.info(
                f"Created custom status: {custom_status.status_name} for project {project_id}"
            )
            return custom_status

        except Exception as e:
            logger.error(f"Error creating custom project status: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def update_custom_project_status(
        db: AsyncSession,
        status_id: int,
        project_id: int,
        display_name: str = None,
        description: str = None,
        color: str = None,
        is_final: bool = None,
        is_active: bool = None,
    ) -> ProjectCustomStatus:
        """Update an existing custom project status"""
        try:
            query = select(ProjectCustomStatus).where(
                ProjectCustomStatus.id == status_id,
                ProjectCustomStatus.project_id == project_id,
            )
            result = await db.execute(query)
            custom_status = result.scalar_one_or_none()

            if not custom_status:
                raise ValueError(
                    f"Custom status with ID {status_id} not found for project {project_id}"
                )

            if display_name is not None:
                custom_status.display_name = display_name
            if description is not None:
                custom_status.description = description
            if color is not None:
                custom_status.color = color
            if is_final is not None:
                custom_status.is_final = is_final
            if is_active is not None:
                custom_status.is_active = is_active

            await db.commit()
            await db.refresh(custom_status)

            logger.info(
                f"Updated custom status: {custom_status.status_name} for project {project_id}"
            )
            return custom_status

        except Exception as e:
            logger.error(f"Error updating custom project status: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_custom_project_status(
        db: AsyncSession, status_id: int, project_id: int
    ) -> bool:
        """Delete (deactivate) a custom project status"""
        try:
            query = select(ProjectCustomStatus).where(
                ProjectCustomStatus.id == status_id,
                ProjectCustomStatus.project_id == project_id,
            )
            result = await db.execute(query)
            custom_status = result.scalar_one_or_none()

            if not custom_status:
                raise ValueError(
                    f"Custom status with ID {status_id} not found for project {project_id}"
                )

            # Check if any tasks are using this status
            tasks_with_status_query = text(
                "SELECT COUNT(*) FROM tasks WHERE project_id = :project_id AND status = :status_name"
            )
            try:
                result = await db.execute(
                    tasks_with_status_query,
                    {
                        "project_id": project_id,
                        "status_name": custom_status.status_name,
                    },
                )
                task_count = result.scalar()
            except Exception:
                # If the status is not in the enum, it can't be used by any tasks
                await db.rollback()
                task_count = 0

            if task_count > 0:
                # Deactivate instead of delete if tasks are using it
                custom_status.is_active = False
                await db.commit()
                logger.info(
                    f"Deactivated custom status: {custom_status.status_name} for project {project_id} (used by {task_count} tasks)"
                )
                return False
            else:
                # Safe to delete
                await db.delete(custom_status)
                await db.commit()
                logger.info(
                    f"Deleted custom status: {custom_status.status_name} for project {project_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Error deleting custom project status: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def is_valid_project_status(
        db: AsyncSession, project_id: int, status_name: str
    ) -> bool:
        """Check if a status is valid for a specific project"""
        try:
            statuses = await ProjectStatusService.get_project_statuses(db, project_id)
            return any(status["status_name"] == status_name for status in statuses)
        except Exception as e:
            logger.error(f"Error validating project status: {str(e)}")
            return status_name in DEFAULT_PROJECT_STATUSES

    @staticmethod
    async def get_project_status_display_name(
        db: AsyncSession, project_id: int, status_name: str
    ) -> str:
        """Get display name for a project status"""
        try:
            statuses = await ProjectStatusService.get_project_statuses(db, project_id)
            for status in statuses:
                if status["status_name"] == status_name:
                    return status["display_name"]

            # Fallback
            return status_name.replace("_", " ").title()

        except Exception as e:
            logger.error(f"Error getting display name for project status: {str(e)}")
            return status_name.replace("_", " ").title()

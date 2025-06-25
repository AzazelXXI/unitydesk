import enum
import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from .base import Base


class ActivityType(str, enum.Enum):
    # Project activities
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_STATUS_CHANGED = "project_status_changed"

    # Task activities
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"

    # Member activities
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"

    # File activities
    FILE_UPLOADED = "file_uploaded"
    FILE_DELETED = "file_deleted"

    # Comment activities
    COMMENT_ADDED = "comment_added"


class ProjectActivity(Base):
    __tablename__ = "project_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    activity_type = Column(String(50), nullable=False)  # ActivityType enum value
    description = Column(Text, nullable=False)  # Human-readable description

    # Optional: reference to related entity
    target_entity_type = Column(String(50), nullable=True)  # 'task', 'file', etc.
    target_entity_id = Column(Integer, nullable=True)

    # Optional: extra data as JSON
    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="activities")
    user = relationship("User")

    @staticmethod
    def create_activity(
        project_id: int,
        user_id: int,
        activity_type: ActivityType,
        description: str,
        target_entity_type: str = None,
        target_entity_id: int = None,
        extra_data: dict = None,
    ):
        """Helper method to create activity entries"""
        return ProjectActivity(
            project_id=project_id,
            user_id=user_id,
            activity_type=activity_type.value,
            description=description,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            extra_data=extra_data or {},
        )

    @staticmethod
    def format_activity_icon(activity_type: str) -> str:
        """Return appropriate Bootstrap icon for activity type"""
        icon_map = {
            "project_created": "bi-folder-plus",
            "project_updated": "bi-pencil-square",
            "project_status_changed": "bi-arrow-repeat",
            "task_created": "bi-plus-circle",
            "task_completed": "bi-check-circle",
            "task_status_changed": "bi-arrow-repeat",
            "task_assigned": "bi-person-plus",
            "task_updated": "bi-pencil",
            "member_added": "bi-person-plus-fill",
            "member_removed": "bi-person-dash",
            "file_uploaded": "bi-cloud-upload",
            "file_deleted": "bi-trash",
            "comment_added": "bi-chat-dots",
        }
        return icon_map.get(activity_type, "bi-activity")

    @staticmethod
    def format_activity_color(activity_type: str) -> str:
        """Return appropriate color class for activity type"""
        color_map = {
            "project_created": "success",
            "project_updated": "info",
            "project_status_changed": "warning",
            "task_created": "primary",
            "task_completed": "success",
            "task_status_changed": "warning",
            "task_assigned": "info",
            "task_updated": "secondary",
            "member_added": "success",
            "member_removed": "danger",
            "file_uploaded": "info",
            "file_deleted": "danger",
            "comment_added": "primary",
        }
        return color_map.get(activity_type, "secondary")

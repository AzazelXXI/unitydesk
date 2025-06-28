import enum
import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SAEnum,
    Text,
    Float,
    Numeric,
)
from sqlalchemy.orm import relationship

from .base import Base


class ProjectStatusEnum(str, enum.Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(
        SAEnum(ProjectStatusEnum, name="project_status_enum", create_type=False),
        nullable=False,
        default=ProjectStatusEnum.PLANNING,
    )
    progress = Column(Integer, nullable=False, default=0)  # Progress from 0% to 100%
    budget = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Key
    owner_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Relationships - Align with Class Diagram
    owner = relationship("User", back_populates="owned_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship(
        "Milestone", back_populates="project", cascade="all, delete-orphan"
    )
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Attachment", back_populates="project")
    events = relationship("Event", back_populates="project")
    # Many-to-many relationship for team members
    team_members = relationship(
        "User", secondary="project_members", back_populates="member_projects"
    )
    activities = relationship(
        "ProjectActivity", back_populates="project", cascade="all, delete-orphan"
    )


# Default project statuses - can be extended with custom statuses
DEFAULT_PROJECT_STATUSES = [
    "Planning",
    "In Progress",
    "Completed",
    "Canceled",
]


# Helper function to get all available project statuses (default + custom)
def get_available_project_statuses():
    """
    Get all available project statuses including default and custom statuses.
    This can be extended to fetch custom statuses from database or configuration.
    For now, returns default statuses. Use ProjectStatusService for full functionality.
    """
    return DEFAULT_PROJECT_STATUSES.copy()


# Helper function to validate project status
def is_valid_project_status(project_status: str) -> bool:
    """Validate if a project status is allowed (basic validation for default statuses)"""
    return project_status in DEFAULT_PROJECT_STATUSES


# Helper function to get display name for project status
def get_project_status_display_name(project_status: str) -> str:
    """Get display name for project status (fallback for when DB is not available)"""
    return project_status.title()


# Helper function to get status color
def get_project_status_color(project_status: str) -> str:
    """Get color for project status for UI display"""
    status_colors = {
        "Planning": "#6c757d",  # Gray
        "In Progress": "#007bff",  # Blue
        "Completed": "#28a745",  # Green
        "Canceled": "#dc3545",  # Red
    }
    return status_colors.get(project_status, "#6c757d")

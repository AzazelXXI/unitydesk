"""
Project-Specific Custom Status Model - Allows projects to have their own custom statuses
"""

import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import validates, relationship

from .base import Base


class ProjectCustomStatus(Base):
    """Model for storing custom statuses specific to individual projects"""

    __tablename__ = "custom_project_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    status_name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True, default="#007bff")  # Hex color for UI
    is_active = Column(Boolean, default=True, nullable=False)
    is_final = Column(
        Boolean, default=False, nullable=False
    )  # For statuses like "Completed", "Canceled"
    sort_order = Column(Integer, default=0, nullable=False)  # For ordering in dropdowns
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationship to project
    # project = relationship("Project", back_populates="custom_statuses")

    # Unique constraint: status_name must be unique within a project
    __table_args__ = (
        UniqueConstraint("project_id", "status_name", name="uq_project_status_name"),
    )

    @validates("status_name")
    def validate_status_name(self, key, status_name):
        """Ensure status_name follows naming conventions"""
        if not status_name:
            raise ValueError("Status name cannot be empty")

        # Keep original case but remove spaces and special characters for internal use
        cleaned_name = status_name.replace(" ", "_").replace("-", "_")

        # Remove any non-alphanumeric characters except underscores
        import re

        cleaned_name = re.sub(r"[^a-zA-Z0-9_]", "", cleaned_name)

        if len(cleaned_name) < 2:
            raise ValueError("Status name must be at least 2 characters long")

        return cleaned_name

    @validates("color")
    def validate_color(self, key, color):
        """Ensure color is a valid hex color"""
        if color and not color.startswith("#"):
            color = "#" + color

        if color:
            import re

            if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
                return "#007bff"  # Default blue

        return color or "#007bff"

    def __repr__(self):
        return f"<ProjectCustomStatus(project_id={self.project_id}, status_name='{self.status_name}', display_name='{self.display_name}')>"

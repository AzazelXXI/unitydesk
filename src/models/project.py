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

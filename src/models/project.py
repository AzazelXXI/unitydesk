import enum
import datetime
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    DateTime,
    Enum as SAEnum,
    Text,
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

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False, index=True)
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
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    # User could create many Project
    creator = relationship("User", back_populates="created_projects")
    
    # A Project has many Tasks
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    # Many Team has many Project
    team_project_created = relationship("Team", back_populates="team_project_creator", foreign_keys="[Team.project_id]")
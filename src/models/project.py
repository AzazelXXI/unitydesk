import enum
import datetime
import uuid
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
    UUID,
)
from sqlalchemy.orm import relationship

from .base import Base
from .association_tables import project_teams_table


class ProjectStatusEnum(str, enum.Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
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
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationship
    owner = relationship("User", back_populates="owned_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    teams = relationship(
        "Team", secondary=project_teams_table, back_populates="projects"
    )
    events = relationship("Event", back_populates="project")

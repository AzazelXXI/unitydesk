import enum
import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as SAEnum,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from .base import Base


class MilestoneStatusEnum(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"


class Milestone(Base):
    """
    Milestone model for project milestones
    """

    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SAEnum(MilestoneStatusEnum, name="milestone_status_enum", create_type=False),
        nullable=False,
        default=MilestoneStatusEnum.NOT_STARTED,
    )
    target_date = Column(DateTime, nullable=False)
    completion_date = Column(DateTime, nullable=True)
    is_critical = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="milestones")

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
)
from sqlalchemy.orm import relationship

from .base import Base


class RiskPriorityEnum(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskStatusEnum(str, enum.Enum):
    IDENTIFIED = "Identified"
    MONITORING = "Monitoring"
    MITIGATED = "Mitigated"
    OCCURRED = "Occurred"
    CLOSED = "Closed"


class Risk(Base):
    """
    Risk model for project risk management
    """

    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    impact = Column(Text, nullable=True)  # Description of potential impact
    mitigation_plan = Column(Text, nullable=True)  # How to mitigate the risk
    priority = Column(
        SAEnum(RiskPriorityEnum, name="risk_priority_enum", create_type=False),
        nullable=False,
        default=RiskPriorityEnum.MEDIUM,
    )
    status = Column(
        SAEnum(RiskStatusEnum, name="risk_status_enum", create_type=False),
        nullable=False,
        default=RiskStatusEnum.IDENTIFIED,
    )
    probability = Column(Integer, nullable=True)  # 1-100 scale
    impact_score = Column(Integer, nullable=True)  # 1-100 scale
    identified_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    target_resolution_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Risk owner

    # Relationships
    project = relationship("Project", back_populates="risks")
    owner = relationship("User")

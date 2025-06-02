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
    UUID,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .base import Base


class UserStatusEnum(str, enum.Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    IDLE = "Idle"


class UserTypeEnum(str, enum.Enum):
    PROJECT_MANAGER = "ProjectManager"
    TEAM_MEMBER = "TeamMember"
    CLIENT = "Client"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(
        SAEnum(UserStatusEnum, name="user_status_enum", create_type=False),
        nullable=False,
        default=UserStatusEnum.OFFLINE,
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    update_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    user_type = Column(
        SAEnum(UserTypeEnum, name="user_type_enum", create_type=False), nullable=False
    )

    __mapper_args = {
        # Value for superclass (if it does contain)
        "polymorphic_identity": "user",
        # Column use to determine subclass
        "polymorphic_on": user_type,
    }

    # Foreign Key
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationships
    owned_projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", back_populates="assignee")
    comments = relationship("Comment", back_populates="author")
    uploaded_attachments = relationship("Attachment", back_populates="uploader")
    created_teams = relationship("Team", back_populates="team_creator")
    calendars = relationship(
        "Calendar", back_populates="user", cascade="all, delete-orphan"
    )


class ProjectManagerUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.PROJECT_MANAGER}


class TeamMemberUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.TEAM_MEMBER}


class ClientUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.CLIENT}

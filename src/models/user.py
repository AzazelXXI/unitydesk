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
)
from sqlalchemy.orm import relationship

from .base import Base


class UserStatusEnum(str, enum.Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    IDLE = "Idle"


class UserTypeEnum(str, enum.Enum):
    USER = "user"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEADER = "team_leader"
    DEVELOPER = "developer"
    TESTER = "tester"
    DESIGNER = "designer"
    SYSTEM_ADMIN = "system_admin"
    TEAM_MEMBER = "team_member"  # Generic team member


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False)  # Polymorphic discriminator
    status = Column(SAEnum(UserStatusEnum), default=UserStatusEnum.OFFLINE)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(
        DateTime, nullable=True
    )  # Relationships - Align with Class Diagram
    owned_projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship(
        "Task", secondary="task_assignees", back_populates="assignees"
    )
    comments = relationship("Comment", back_populates="author")
    uploaded_attachments = relationship("Attachment", back_populates="uploader")
    notifications = relationship("Notification", back_populates="user")
    calendars = relationship("Calendar", back_populates="user")
    # Many-to-many relationship for project membership
    member_projects = relationship(
        "Project", secondary="project_members", back_populates="team_members"
    )

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": user_type,
    }


# Subclasses
class ProjectManager(User):
    __mapper_args__ = {"polymorphic_identity": "project_manager"}


class TeamLeader(User):
    __mapper_args__ = {"polymorphic_identity": "team_leader"}


class Developer(User):
    __mapper_args__ = {"polymorphic_identity": "developer"}


class Tester(User):
    __mapper_args__ = {"polymorphic_identity": "tester"}


class Designer(User):
    __mapper_args__ = {"polymorphic_identity": "designer"}


class SystemAdmin(User):
    __mapper_args__ = {"polymorphic_identity": "system_admin"}

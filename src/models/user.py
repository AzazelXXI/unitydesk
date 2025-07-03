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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(SAEnum(UserStatusEnum), default=UserStatusEnum.OFFLINE)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
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
    profile = relationship("UserProfile", back_populates="user", uselist=False)

    # Department relationships - commented out to prevent startup errors
    # managed_departments = relationship("Department", back_populates="manager")
    # department_memberships = relationship("DepartmentMembership", back_populates="user", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": "user",
    }


class UserProfile(Base):
    """User profile model for additional user information"""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True, default="UTC")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationship back to User
    user = relationship("User", back_populates="profile")

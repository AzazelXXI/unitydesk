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


# Keep the enum for backward compatibility but use list-based approach for flexibility
class UserTypeEnum(str, enum.Enum):
    USER = "user"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEADER = "team_leader"
    DEVELOPER = "developer"
    TESTER = "tester"
    DESIGNER = "designer"
    SYSTEM_ADMIN = "system_admin"
    TEAM_MEMBER = "team_member"  # Generic team member


# Default user types - can be extended with custom types
# This list maintains the original enum values but allows for dynamic extension
DEFAULT_USER_TYPES = [
    "user",
    "project_manager",
    "team_leader",
    "developer",
    "tester",
    "designer",
    "system_admin",
    "team_member",
]


# Helper functions for backward compatibility (use UserTypeService for full functionality)
def get_available_user_types():
    """
    Get default user types for backward compatibility.
    For full functionality including custom types, use UserTypeService.get_all_user_types()
    """
    return DEFAULT_USER_TYPES.copy()


def is_valid_user_type(user_type: str) -> bool:
    """
    Validate if a user type is in the default list (basic validation).
    For full validation including custom types, use UserTypeService.is_valid_user_type()
    """
    return user_type in DEFAULT_USER_TYPES


def get_user_type_display_name(user_type: str) -> str:
    """
    Get display name for user type (fallback for when DB is not available).
    For full functionality, use UserTypeService.get_user_type_display_name()
    """
    return user_type.replace("_", " ").title()


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
    )  # Relationship to UserProfile
    profile = relationship("UserProfile", back_populates="user", uselist=False)

    # Department relationships - commented out to prevent startup errors
    # managed_departments = relationship("Department", back_populates="manager")
    # department_memberships = relationship("DepartmentMembership", back_populates="user", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": user_type,
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

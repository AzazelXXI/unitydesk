from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Text,
    Enum,
    Integer,
    DateTime,
)
from sqlalchemy.orm import relationship, remote, backref, foreign
import enum
from datetime import datetime

from src.database import Base
from src.models.base import RootModel


class UserRole(str, enum.Enum):
    """Enum for user roles in the system"""

    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"
    GUEST = "guest"


class User(Base, RootModel):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_id = Column(String(50), unique=True, nullable=True)
    hire_date = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    primary_department = relationship(
        "Department", foreign_keys=[department_id], back_populates="primary_members"
    )
    position = relationship("Position", back_populates="users")
    manager = relationship(
        "User",
        primaryjoin="User.manager_id == User.id",
        remote_side="[User.id]",
        foreign_keys=[manager_id],
        back_populates="direct_reports",
    )

    direct_reports = relationship(  # Thêm định nghĩa mới
        "User",
        back_populates="manager",
        foreign_keys="[User.manager_id]",  # Không cần remote_side ở phía này
    )

    department_memberships = relationship(
        "DepartmentMembership", back_populates="user", cascade="all, delete-orphan"
    )
    owned_chats = relationship("Chat", back_populates="owner")
    messages = relationship("Message", back_populates="sender")
    chat_memberships = relationship("ChatMember", back_populates="user")
    calendars = relationship("Calendar", back_populates="owner")
    events = relationship("Event", back_populates="organizer")
    event_participations = relationship("EventParticipant", back_populates="user")
    documents = relationship("Document", back_populates="owner")
    folders = relationship("Folder", back_populates="owner")
    tasks_created = relationship(
        "Task", foreign_keys="Task.creator_id", back_populates="creator"
    )
    task_assignments = relationship("TaskAssignee", back_populates="user")
    projects_owned = relationship("Project", back_populates="owner")


class UserProfile(Base, RootModel):
    """Extended information about a user"""

    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(255))
    avatar_url = Column(String(255))
    bio = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)

    user = relationship("User", back_populates="profile")


class Department(Base, RootModel):
    """Department model for organizational structure"""

    __tablename__ = "departments"

    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    head_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    path = Column(
        String(255), nullable=True
    )  # Materialized path for efficient hierarchy queries
    level = Column(Integer, default=0)  # Hierarchy level (0=root, 1=division, etc.)

    # Relationships
    parent = relationship(
        "Department",
        primaryjoin="Department.parent_id == Department.id",
        remote_side="[Department.id]",
        foreign_keys=[parent_id],
        back_populates="subdepartments",  # Thay backref bằng back_populates
    )

    subdepartments = relationship(  # Thêm định nghĩa mới
        "Department",
        back_populates="parent",
        foreign_keys="[Department.parent_id]",
    )
    head = relationship("User", foreign_keys=[head_user_id])
    primary_members = relationship(
        "User", back_populates="primary_department", foreign_keys="User.department_id"
    )
    positions = relationship("Position", back_populates="department")
    memberships = relationship(
        "DepartmentMembership",
        back_populates="department",
        cascade="all, delete-orphan",
    )


class Position(Base, RootModel):
    """Position model for job roles within the organization"""

    __tablename__ = "positions"

    title = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    description = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)
    grade_level = Column(Integer, default=0)  # Hierarchical positioning
    is_managerial = Column(Boolean, default=False)
    reports_to_position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    # Relationships
    department = relationship("Department", back_populates="positions")
    reports_to = relationship(
        "Position",
        primaryjoin="Position.reports_to_position_id == Position.id",
        remote_side="[Position.id]",
        foreign_keys=[reports_to_position_id],
        back_populates="subordinate_positions",  # Thay backref bằng back_populates
    )

    subordinate_positions = relationship(  # Thêm định nghĩa mới
        "Position",
        back_populates="reports_to",
        foreign_keys="[Position.reports_to_position_id]",
    )
    users = relationship("User", back_populates="position")


class DepartmentMembership(Base, RootModel):
    """Many-to-many relationship between users and departments"""

    __tablename__ = "department_memberships"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    is_primary = Column(Boolean, default=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    phone_number = Column(String(50), nullable=True)
    position_title = Column(
        String(100), nullable=True
    )  # Đổi tên để không trùng với relationship 'position'
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")

    # Relationships
    user = relationship("User", back_populates="department_memberships")
    department = relationship("Department", back_populates="memberships")

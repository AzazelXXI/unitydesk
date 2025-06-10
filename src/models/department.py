"""
Department Models

This module defines the database models for departments, positions, and department memberships.
These models are used for organizational structure and user role management.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base


class Department(Base):
    """
    Department model for organizational structure.

    Represents departments within the organization with hierarchy support.
    """

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships
    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship("Department", back_populates="parent")
    # manager = relationship("User", back_populates="managed_departments")  # Commented out to prevent circular reference
    positions = relationship(
        "Position", back_populates="department", cascade="all, delete-orphan"
    )
    memberships = relationship(
        "DepartmentMembership",
        back_populates="department",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_department_parent_active", "parent_id", "is_active"),
        Index("idx_department_manager", "manager_id"),
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"


class Position(Base):
    """
    Position model for job positions within departments.

    Represents specific roles or positions that users can hold within departments.
    """

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    level = Column(Integer, default=1, nullable=False)  # Organizational level/seniority

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="positions")
    memberships = relationship(
        "DepartmentMembership", back_populates="position", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_position_department_active", "department_id", "is_active"),
        Index("idx_position_level", "level"),
    )

    def __repr__(self):
        return f"<Position(id={self.id}, title='{self.title}', department_id={self.department_id})>"


class DepartmentMembership(Base):
    """
    Department membership model for user-department-position relationships.

    Represents the association between users, departments, and their positions,
    supporting multiple memberships and role assignments.
    """

    __tablename__ = "department_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)

    # Membership details
    start_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_primary = Column(
        Boolean, default=False, nullable=False
    )  # Primary department for user
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Relationships
    # user = relationship("User", back_populates="department_memberships")  # Commented out to prevent circular reference
    department = relationship("Department", back_populates="memberships")
    position = relationship("Position", back_populates="memberships")

    # Indexes
    __table_args__ = (
        Index("idx_membership_user_active", "user_id", "is_active"),
        Index("idx_membership_department_active", "department_id", "is_active"),
        Index("idx_membership_user_primary", "user_id", "is_primary"),
        Index("idx_membership_dates", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<DepartmentMembership(id={self.id}, user_id={self.user_id}, department_id={self.department_id}, position_id={self.position_id})>"

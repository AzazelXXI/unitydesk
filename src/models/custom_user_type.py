"""
Custom User Type Model - Allows dynamic user type management
"""

import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import validates

from .base import Base


class CustomUserType(Base):
    """Model for storing custom user types"""

    __tablename__ = "custom_user_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    @validates("type_name")
    def validate_type_name(self, key, type_name):
        """Ensure type_name follows naming conventions"""
        if not type_name:
            raise ValueError("Type name cannot be empty")

        # Convert to lowercase and replace spaces with underscores
        cleaned_name = type_name.lower().replace(" ", "_").replace("-", "_")

        # Remove any non-alphanumeric characters except underscores
        import re

        cleaned_name = re.sub(r"[^a-z0-9_]", "", cleaned_name)

        if len(cleaned_name) < 2:
            raise ValueError("Type name must be at least 2 characters long")

        return cleaned_name

    def __repr__(self):
        return f"<CustomUserType(type_name='{self.type_name}', display_name='{self.display_name}')>"

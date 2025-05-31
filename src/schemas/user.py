from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models_backup.user import UserRole


# Base user schemas
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    """Base schema for user profile information"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None
    timezone: str = "UTC"


class UserProfileCreate(UserProfileBase):
    """Schema for creating a user profile"""

    pass


class UserProfileUpdate(UserProfileBase):
    """Schema for updating a user profile"""

    pass


class UserProfileRead(UserProfileBase, BaseSchema):
    """Schema for reading a user profile"""

    user_id: int


class UserBase(BaseModel):
    """Base schema for user information"""

    email: EmailStr
    username: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str
    profile: Optional[UserProfileCreate] = None

    @validator("password")
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    profile: Optional[UserProfileUpdate] = None


class UserResponse(UserBase, BaseSchema):
    """Schema for reading user information"""

    profile: Optional[UserProfileRead] = None


class UserWithPassword(UserResponse):
    """Schema for user with hashed password (for internal use only)"""

    hashed_password: str


# Authentication schemas
class Token(BaseModel):
    """Schema for authentication token"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 1800  # Default 30 minutes in seconds


class TokenData(BaseModel):
    """Schema for token data"""

    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Schema for login request"""

    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""

    current_password: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, v, values):
        """Validate new password strength and ensure it's different from old password"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""

    email: EmailStr

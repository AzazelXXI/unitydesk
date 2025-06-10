from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.user import User, ProjectManager
from src.middleware.auth_middleware import get_current_user as auth_get_current_user


async def get_current_user(current_user: User = Depends(auth_get_current_user)) -> User:
    """Get current authenticated user using the main auth system"""
    return current_user


async def require_project_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to be a Project Manager"""
    if not isinstance(current_user, ProjectManager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Project Managers can perform this action",
        )
    return current_user

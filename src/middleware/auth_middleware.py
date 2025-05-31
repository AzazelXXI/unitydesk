from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models_backup.user import UserRole, User
from src.schemas.user import TokenData
from src.services.auth_service import verify_token
import logging

# Set up OAuth2 for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

logger = logging.getLogger(__name__)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current user from the provided token.
    """
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = await verify_token(token)
        if token_data is None:
            raise credentials_exception

        # Query DB for user
        query = await db.execute(
            User.__table__.select().where(User.id == token_data.user_id)
        )
        user = query.scalars().first()

        if user is None:
            raise credentials_exception

        # Check if user is still active
        if not user.is_active:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Inactive user")

        return user
    except JWTError:
        logger.error("JWT validation error", exc_info=True)
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def role_required(allowed_roles: List[UserRole]):
    """
    Check if user has one of the required roles.
    """

    async def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    return role_dependency


class RoleChecker:
    """
    Check user roles on class-based views.
    """

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return user


# Admin-only dependency
admin_only = role_required([UserRole.ADMIN])

# Admin or manager dependency
admin_or_manager = role_required([UserRole.ADMIN, UserRole.MANAGER])

# Allow anyone but guest
non_guest = role_required([UserRole.ADMIN, UserRole.MANAGER, UserRole.USER])

# Allow anyone but guest
non_guest = role_required([UserRole.ADMIN, UserRole.MANAGER, UserRole.USER])

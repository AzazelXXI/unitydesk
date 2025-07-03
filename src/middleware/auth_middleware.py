from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import os

from src.database import get_db
from src.models.user import User, UserStatusEnum

# JWT constants
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "YOUR_SECRET_KEY_HERE_CHANGE_IN_PRODUCTION")
ALGORITHM = "HS256"


class RedirectToLoginException(Exception):
    """Custom exception to trigger redirect to login page for web routes"""

    def __init__(self, message: str = "Authentication required"):
        self.message = message
        super().__init__(self.message)


from src.schemas.user import TokenData
from src.services.auth_service import verify_token
import logging

# Set up OAuth2 for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/auth/login")

logger = logging.getLogger(__name__)


async def get_current_user_web(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current user from cookie-based authentication for web routes.
    This function checks for the token in cookies instead of Authorization headers.
    For web routes, raises RedirectToLoginException instead of returning JSON errors.
    """
    try:
        # Try to get token from cookie first
        token = request.cookies.get("remember_token")
        logger.debug(f"Cookie token found: {token is not None}")

        if not token:
            # If no cookie token, try Authorization header as fallback
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                logger.debug("Using Authorization header token")
            else:
                logger.debug("No token found in cookies or headers - needs login")
                raise RedirectToLoginException("No authentication token found")

        logger.debug("Attempting to verify token")
        token_data = await verify_token(token)
        if token_data is None:
            logger.warning("Token verification failed - needs login")
            raise RedirectToLoginException("Invalid or expired token")

        logger.debug(f"Token verified for user_id: {token_data.user_id}")

        # Query DB for user using proper SQLAlchemy async syntax
        result = await db.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning("User not found in database - needs login")
            raise RedirectToLoginException("User not found")

        # Check if user is not offline - allow ONLINE and IDLE status
        if user.status == UserStatusEnum.OFFLINE:
            logger.warning(f"User is offline, status: {user.status} - needs login")
            raise RedirectToLoginException("User is offline")

        logger.debug(f"Successfully authenticated user: {user.name}")
        return user

    except RedirectToLoginException:
        # Re-raise custom redirect exceptions as-is
        raise
    except JWTError as e:
        logger.warning(f"JWT validation error in web auth: {e} - needs login")
        raise RedirectToLoginException("Invalid token format")
    except Exception as e:
        logger.error(f"Error in web authentication: {e} - needs login", exc_info=True)
        raise RedirectToLoginException("Authentication error")


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

        # Query DB for user using proper SQLAlchemy async syntax
        result = await db.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        # Check if user is not offline
        if user.status == UserStatusEnum.OFFLINE:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="User is offline"
            )

        return user
    except JWTError:
        logger.error("JWT validation error", exc_info=True)
        raise credentials_exception


async def get_current_user_from_cookie(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current user from cookie token (for API endpoints called from web interface).
    """
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Get token from cookie
        token = request.cookies.get("remember_token")
        if not token:
            logger.warning("No remember_token cookie found")
            raise credentials_exception

        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        logger.error("JWT validation error from cookie", exc_info=True)
        raise credentials_exception

    # Get user from database
    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalars().first()
    if user is None:
        raise credentials_exception

    # Check if user is not offline
    if user.status == UserStatusEnum.OFFLINE:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User is offline")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    """
    # User is already checked for active status in get_current_user
    return current_user


def role_required():
    """
    Placeholder for role checks, now removed.
    """

    async def role_dependency(current_user: User = Depends(get_current_user)):
        return current_user

    return role_dependency


class RoleChecker:
    """
    Placeholder for role checks, now removed.
    """

    async def __call__(self, request: Request, user: User = Depends(get_current_user)):
        return user

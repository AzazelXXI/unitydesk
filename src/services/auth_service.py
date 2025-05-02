from datetime import datetime, timedelta
from typing import Optional
import os
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user import TokenData, UserResponse, UserWithPassword
import logging

# Configure JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "YOUR_SECRET_KEY_HERE_CHANGE_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for secure storage.
    """
    return pwd_context.hash(password)


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """
    Authenticate a user by username and password.
    """
    try:
        # Get user by username or email
        query = await db.execute(
            select(User).where((User.username == username) | (User.email == username))
        )
        user = query.scalars().first()

        if not user:
            logger.info(
                f"Authentication failed: No user found with username/email {username}"
            )
            return None

        if not verify_password(password, user.hashed_password):
            logger.info(f"Authentication failed: Invalid password for user {username}")
            return None

        return user
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}", exc_info=True)
        return None


async def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token for a user.
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    # Create and sign JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify a JWT token and return the token data.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        if username is None or user_id is None:
            return None

        return TokenData(username=username, user_id=user_id, role=role)
    except JWTError:
        return None
    except JWTError:
        return None

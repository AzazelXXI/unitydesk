from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import os
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# Real model imports
from src.models.user import User

from src.schemas.user import TokenData, UserResponse, UserWithPassword
import logging

# Load environment variables
load_dotenv()

# Configure JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "YOUR_SECRET_KEY_HERE_CHANGE_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

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
        # Get user by name or email (User model uses 'name' instead of 'username')
        query = await db.execute(
            select(User).where((User.name == username) | (User.email == username))
        )
        user = query.scalars().first()

        if not user:
            logger.info(
                f"Authentication failed: No user found with username/email {username}"
            )
            return None

        if not verify_password(password, user.password_hash):
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

    # Add expiration time and token type
    to_encode.update({"exp": expire, "token_type": "access"})

    # Create and sign JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def create_refresh_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token for a user.
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # Add expiration time and token type
    to_encode.update({"exp": expire, "token_type": "refresh"})

    # Create and sign JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify a JWT token and return the token data.
    Args:
        token: The JWT token to verify
        token_type: The expected token type ("access" or "refresh")
    """
    try:
        logger.info(
            f"Attempting to verify token (length: {len(token) if token else 0})"
        )
        logger.info(f"Using SECRET_KEY (length: {len(SECRET_KEY)})")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token payload decoded successfully: {payload}")

        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        actual_token_type: str = payload.get(
            "token_type", "access"
        )  # Default for backward compatibility        logger.info(f"Token claims - username: {username}, user_id: {user_id}, role: {role}, token_type: {actual_token_type}")

        # Validate required fields
        if username is None or user_id is None:
            logger.warning(f"Token validation failed: Missing required claims")
            return None

        # Validate token type if specified
        if token_type and actual_token_type != token_type:
            logger.warning(
                f"Token validation failed: Expected {token_type} token but got {actual_token_type}"
            )
            return None

        # Convert role string to enum if role is present
        from src.models.user import UserTypeEnum

        role_enum = None
        if role:
            try:
                role_enum = UserTypeEnum(role)  # Convert string to enum
            except ValueError:
                logger.warning(f"Invalid role value in token: {role}")

        logger.info("Token validation successful")
        return TokenData(username=username, user_id=user_id, role=role_enum)
    except jwt.ExpiredSignatureError:
        logger.info("Token validation failed: Token has expired")
        return None
    except JWTError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        return None

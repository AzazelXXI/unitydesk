from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import exists
from fastapi import HTTPException, status, Depends
from datetime import timedelta
from typing import List, Optional

from src.database import get_db

# Real model imports
from src.models.user import User, UserProfile, UserTypeEnum as UserRole

from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileCreate,
    UserProfileUpdate,
    Token,
    TokenData,
)
from src.services.auth_service import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

import logging

logger = logging.getLogger(__name__)


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user
    """
    # Check if name or email already exists (User model uses 'name' not 'username')
    query = await db.execute(
        select(
            exists().where(
                (User.name == user_data.name) | (User.email == user_data.email)
            )
        )
    )
    user_exists = query.scalar()

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # Create user with hashed password
    hashed_password = get_password_hash(user_data.password)

    db_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password,
        user_type=user_data.user_type,  # Use enum directly, not .value
        status=user_data.status,
    )

    db.add(db_user)
    await db.flush()

    # Create profile if provided
    if user_data.profile:
        db_profile = UserProfile(
            user_id=db_user.id,
            first_name=user_data.profile.first_name,
            last_name=user_data.profile.last_name,
            display_name=user_data.profile.display_name,
            avatar_url=user_data.profile.avatar_url,
            bio=user_data.profile.bio,
            phone=user_data.profile.phone_number,
            location=user_data.profile.department,
            timezone=user_data.profile.timezone,
        )
        db.add(db_profile)

    await db.commit()
    await db.refresh(db_user)

    return db_user


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None
) -> List[User]:
    """
    Get all users with optional filtering
    """
    query = select(User).options(joinedload(User.profile))

    if role:
        query = query.filter(User.role == role)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get a user by ID
    """
    query = await db.execute(
        select(User).options(joinedload(User.profile)).filter(User.id == user_id)
    )
    return query.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get a user by username
    """
    query = await db.execute(
        select(User).options(joinedload(User.profile)).filter(User.username == username)
    )
    return query.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email
    """
    query = await db.execute(
        select(User).options(joinedload(User.profile)).filter(User.email == email)
    )
    return query.scalars().first()


async def update_user(
    db: AsyncSession, user_id: int, user_data: UserUpdate
) -> Optional[User]:
    """
    Update a user
    """
    # Check if user exists
    user = await get_user(db, user_id)
    if not user:
        return None

    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    profile_data = update_data.pop("profile", None)

    if update_data:
        await db.execute(update(User).where(User.id == user_id).values(**update_data))

    # Update profile if provided
    if profile_data:
        profile_update = {k: v for k, v in profile_data.items() if v is not None}
        if profile_update:
            if user.profile:
                await db.execute(
                    update(UserProfile)
                    .where(UserProfile.user_id == user_id)
                    .values(**profile_update)
                )
            else:
                # Create profile if it doesn't exist
                db_profile = UserProfile(user_id=user_id, **profile_update)
                db.add(db_profile)

    await db.commit()

    # Refresh and return updated user
    return await get_user(db, user_id)


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Delete a user
    """
    # Check if user exists
    user = await get_user(db, user_id)
    if not user:
        return False

    # Delete user
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    return True


async def login_for_access_token(
    db: AsyncSession, username: str, password: str
) -> Optional[Token]:
    """
    Authenticate user and create access and refresh tokens
    """
    user = await authenticate_user(db, username, password)
    if not user:
        logger.info(f"Failed login attempt for username: {username}")
        return None

    # Create token with user info - handle user_type properly
    # Check if user_type is already a string or if it's an enum
    role_value = (
        user.user_type.value if hasattr(user.user_type, "value") else user.user_type
    )
    token_data = {"sub": user.name, "id": user.id, "role": role_value}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)

    access_token = await create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    refresh_token = await create_refresh_token(
        data=token_data, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
    )


async def change_user_password(
    db: AsyncSession, user_id: int, current_password: str, new_password: str
) -> bool:
    """
    Change a user's password after verifying current password
    """  # Get user
    query = await db.execute(select(User).filter(User.id == user_id))
    user = query.scalars().first()

    if not user:
        return False

    # Verify current password using correct field name (User model uses 'name' not 'username')
    if not await authenticate_user(db, user.name, current_password):
        return False

    # Update password using correct field name (User model uses 'password_hash' not 'hashed_password')
    hashed_password = get_password_hash(new_password)
    await db.execute(
        update(User).where(User.id == user_id).values(password_hash=hashed_password)
    )
    await db.commit()

    return True

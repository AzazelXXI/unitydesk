from fastapi import APIRouter, Depends, HTTPException, status, Body, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.models_backup.user import User, UserRole
from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileRead,
    Token,
)
from src.controllers.user_controller import (
    create_user,
    get_users,
    get_user,
    update_user,
    delete_user,
    login_for_access_token,
    change_user_password,
)
from src.middleware.auth_middleware import (
    get_current_active_user,
    admin_only,
    admin_or_manager,
)
from src.middleware.rate_limit import login_rate_limit, register_rate_limit

import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/auth/register",
    response_model=UserResponse,
    dependencies=[Depends(register_rate_limit)],
)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account
    """
    try:
        user = await create_user(db, user_data)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        )


@router.post(
    "/auth/login", response_model=Token, dependencies=[Depends(login_rate_limit)]
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token
    """
    token = await login_for_access_token(db, form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current logged in user info
    """
    return current_user


@router.put("/users/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user's information
    """
    # Don't allow users to change their own role
    if user_update.role is not None:
        user_update.role = current_user.role

    updated_user = await update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user


@router.post("/users/me/change-password", response_model=dict)
async def update_user_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password
    """
    success = await change_user_password(
        db, current_user.id, current_password, new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    return {"message": "Password updated successfully"}


@router.get("/users", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_or_manager),
):
    """
    Get all users (admin/manager only)
    """
    users = await get_users(db, skip=skip, limit=limit, role=role)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_or_manager),
):
    """
    Get specific user by ID (admin/manager only)
    """
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),  # Only admins can update other users
):
    """
    Update a user by ID (admin only)
    """
    updated_user = await update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),  # Only admins can delete users
):
    """
    Delete a user (admin only)
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {"message": "User deleted successfully"}

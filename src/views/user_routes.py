"""
User Web Routes Module

This module handles web routes for user management in the admin panel.
It also provides routes for authentication and user account management.
"""

from fastapi import APIRouter, Depends, Request, Response, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os

from src.database import get_db

# Temporarily commenting out model imports as we use Any placeholders
# from src.models.user import User, UserTypeEnum as UserRole

# Using Any as placeholders for models to allow the application to start
from typing import Any

User = Any
UserRole = Any
from src.schemas.user import UserUpdate, UserCreate
from src.controllers.user_controller import (
    get_users,
    get_user,
    update_user,
    create_user,
    delete_user,
)
from src.middleware.auth_middleware import get_current_user, admin_only

# Set up templates
templates_path = os.path.join(os.path.dirname(__file__), "user", "templates")
templates = Jinja2Templates(directory=templates_path)


router = APIRouter(
    prefix="/user",
    tags=["web-user"],
    responses={404: {"description": "Page not found"}},
)


@router.get("", response_class=HTMLResponse)
async def user_list_view(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role_filter: Optional[UserRole] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Render the user management page.
    """
    try:
        # Calculate pagination values
        skip = (page - 1) * limit

        # Get users with pagination
        users = await get_users(db, skip=skip, limit=limit, role=role_filter)

        # Get total user count for pagination
        # TODO: Implement count query
        total_users = 100  # Placeholder, replace with actual count
        total_pages = (total_users + limit - 1) // limit

        return templates.TemplateResponse(
            "user_list.html",
            {
                "request": request,
                "users": users,
                "current_user": current_user,
                "current_page": page,
                "total_pages": total_pages,
                "role_filter": role_filter,
                "roles": list(UserRole),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/create", response_class=HTMLResponse)
async def create_user_view(request: Request, current_user: User = Depends(admin_only)):
    """
    Render the create user form.
    """
    return templates.TemplateResponse(
        "user_form.html",
        {
            "request": request,
            "current_user": current_user,
            "roles": list(UserRole),
            "is_edit": False,
        },
    )


@router.post("/create", response_class=HTMLResponse)
async def create_user_action(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    display_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """
    Handle user creation form submission.
    """
    try:
        # Create user data model
        user_data = UserCreate(
            email=email,
            username=username,
            password=password,
            role=role,
            profile=(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "display_name": display_name,
                }
                if first_name or last_name or display_name
                else None
            ),
        )

        # Create user
        await create_user(db, user_data)

        # Redirect to user list with success message
        return RedirectResponse(
            url="/user?success=User created successfully", status_code=303
        )
    except Exception as e:
        # Return to form with error message
        return templates.TemplateResponse(
            "user_form.html",
            {
                "request": request,
                "current_user": current_user,
                "roles": list(UserRole),
                "is_edit": False,
                "error": str(e),
                "form_data": {
                    "email": email,
                    "username": username,
                    "role": role,
                    "first_name": first_name,
                    "last_name": last_name,
                    "display_name": display_name,
                },
            },
        )


@router.get("/{user_id}", response_class=HTMLResponse)
async def user_detail_view(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Render user detail view.
    """
    # Only allow users to view themselves unless they are admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        "user_detail.html",
        {"request": request, "user": user, "current_user": current_user},
    )


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_view(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """
    Render user edit form.
    """
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        "user_form.html",
        {
            "request": request,
            "current_user": current_user,
            "user": user,
            "roles": list(UserRole),
            "is_edit": True,
        },
    )


@router.post("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_action(
    request: Request,
    user_id: int,
    email: str = Form(...),
    username: str = Form(...),
    role: UserRole = Form(...),
    is_active: bool = Form(False),
    is_verified: bool = Form(False),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    display_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """
    Handle user edit form submission.
    """
    try:
        # Create update model
        user_update = UserUpdate(
            email=email,
            username=username,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            profile={
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
            },
        )

        # Update user
        updated_user = await update_user(db, user_id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Redirect to user detail page
        return RedirectResponse(
            url=f"/user/{user_id}?success=User updated successfully", status_code=303
        )
    except Exception as e:
        # Get user for form repopulation
        user = await get_user(db, user_id)

        # Return to form with error message
        return templates.TemplateResponse(
            "user_form.html",
            {
                "request": request,
                "current_user": current_user,
                "user": user,
                "roles": list(UserRole),
                "is_edit": True,
                "error": str(e),
            },
        )


@router.post("/{user_id}/delete")
async def delete_user_action(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """
    Handle user deletion.
    """
    # Prevent self-deletion
    if current_user.id == user_id:
        return RedirectResponse(
            url="/user?error=You cannot delete your own account", status_code=303
        )

    success = await delete_user(db, user_id)
    if not success:
        return RedirectResponse(url="/user?error=User not found", status_code=303)

    return RedirectResponse(
        url="/user?success=User deleted successfully", status_code=303
    )


# Authentication and Profile Routes


@router.get("/profile", response_class=HTMLResponse)
async def profile_view(
    request: Request, current_user: User = Depends(get_current_user)
):
    """
    Render the user profile page.
    """
    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": current_user}
    )


@router.post("/profile", response_class=HTMLResponse)
async def update_profile_action(
    request: Request,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    display_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the user's profile information.
    """
    try:
        # Create update model
        user_update = UserUpdate(
            profile={
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
            }
        )

        # Update user
        updated_user = await update_user(db, current_user.id, user_update)

        return RedirectResponse(
            url="/user/profile?success=Profile updated successfully", status_code=303
        )
    except Exception as e:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "current_user": current_user, "error": str(e)},
        )

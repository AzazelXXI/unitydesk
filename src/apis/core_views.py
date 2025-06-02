from fastapi import APIRouter, Depends, HTTPException
from src.controllers.core_controller import CoreController
from src.middleware.auth_middleware import (
    get_current_user,
    admin_only,
    admin_or_manager,
    non_guest,
)
from src.models.user import User  # Changed from src.models_backup.user

router = APIRouter(tags=["core"])
controller = CoreController()


@router.get("/")
async def get_core_info():
    """Get basic information about the core API"""
    return controller.get_core_info()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return controller.health_check()


@router.get("/version")
async def get_version():
    """Get current API version information"""
    return controller.get_version()


@router.get("/authenticated")
async def authenticated_endpoint(current_user: User = Depends(get_current_user)):
    """Example of an authenticated endpoint that requires a valid user token"""
    return {
        "message": "You are authenticated!",
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/admin-only")
async def admin_endpoint(current_user: User = Depends(admin_only)):
    """Example of an admin-only endpoint"""
    return {
        "message": "This is an admin-only endpoint",
        "user_id": current_user.id,
        "username": current_user.username,
    }


@router.get("/manager-plus")
async def manager_endpoint(current_user: User = Depends(admin_or_manager)):
    """Example of an endpoint for admins and managers"""
    return {
        "message": "This is an endpoint for admins and managers",
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }

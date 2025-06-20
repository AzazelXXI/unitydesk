"""
Notification API Routes - Handle user notifications
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from src.database import get_db
from src.middleware.auth_middleware import get_current_user, get_current_user_web
from src.models.user import User
from src.models.notification import Notification, NotificationTypeEnum
from src.services.notification_service import NotificationService
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)


# Create a dependency that works for both API and web requests
async def get_current_user_flexible(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user using either web cookies or API tokens
    """
    try:
        # Try web authentication first (cookies)
        return await get_current_user_web(request, db)
    except Exception:
        try:
            # Fall back to API authentication (Bearer token)
            return await get_current_user(request, db)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


# Router for notification API endpoints
router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for API
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: NotificationTypeEnum
    is_read: bool
    created_at: datetime
    read_at: datetime | None
    task_id: int | None
    project_id: int | None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    request: Request,
    unread_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_flexible),
):
    """
    Get notifications for the current user
    """
    try:
        notifications = await NotificationService.get_user_notifications(
            db=db,
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
        )

        return notifications

    except Exception as e:
        logger.error(f"Error getting notifications for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}",
        )


@router.put("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_flexible),
):
    """
    Mark a notification as read
    """
    try:
        success = await NotificationService.mark_notification_read(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or not owned by user",
            )

        return {"message": "Notification marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}",
        )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get count of unread notifications for the current user
    """
    try:
        notifications = await NotificationService.get_user_notifications(
            db=db,
            user_id=current_user.id,
            unread_only=True,
            limit=1000,  # Get all unread to count them
        )

        return {"unread_count": len(notifications)}

    except Exception as e:
        logger.error(f"Error getting unread count for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}",
        )

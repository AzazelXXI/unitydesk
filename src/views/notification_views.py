from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from src.controllers.notification_controller import NotificationController

router = APIRouter()
controller = NotificationController()

# WebSocket router that will be exported separately
ws_router = APIRouter()

@router.get("/notifications")
async def get_notifications():
    """Get all notifications for the current user"""
    return controller.get_notifications()

@router.post("/notifications")
async def create_notification(notification_data: dict):
    """Create a new notification"""
    return controller.create_notification(notification_data)

@router.get("/notifications/{notification_id}")
async def get_notification(notification_id: int):
    """Get notification by ID"""
    return controller.get_notification(notification_id)

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    return controller.mark_as_read(notification_id)

@ws_router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    await controller.handle_websocket(websocket)

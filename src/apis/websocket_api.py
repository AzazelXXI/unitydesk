"""
WebSocket API endpoints for real-time notifications
"""

import logging
import json
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.user import User
from src.models.project import Project
from src.services.websocket_manager import websocket_manager
from src.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

# WebSocket router
ws_router = APIRouter(prefix="/ws", tags=["websocket"])


@ws_router.websocket("/notifications/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: int, db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications

    Usage from frontend:
    const ws = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}`);
    """
    await websocket_manager.connect(websocket, user_id)

    try:
        # Get user's projects and subscribe to them
        user_projects_query = select(Project).where(
            (Project.owner_id == user_id)
            | (Project.team_members.any(User.id == user_id))
        )
        result = await db.execute(user_projects_query)
        user_projects = result.scalars().all()

        project_ids = [project.id for project in user_projects]
        if project_ids:
            await websocket_manager.subscribe_to_projects(user_id, project_ids, db)

        # Send initial connection message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "message": "Connected to real-time notifications",
                "subscribed_projects": project_ids,
                "timestamp": "now",
            },
        }
        await websocket.send_text(json.dumps(welcome_message))

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive any messages from client (heartbeat, subscription updates, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "heartbeat":
                    await websocket.send_text(
                        json.dumps({"type": "heartbeat_response", "timestamp": "now"})
                    )

                elif message.get("type") == "subscribe_projects":
                    # Allow dynamic subscription to new projects
                    new_project_ids = message.get("project_ids", [])
                    if new_project_ids:
                        await websocket_manager.subscribe_to_projects(
                            user_id, new_project_ids, db
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "subscription_updated",
                                    "data": {"subscribed_projects": new_project_ids},
                                }
                            )
                        )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        websocket_manager.disconnect(user_id)


@ws_router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()

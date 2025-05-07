"""
Meeting Web Router - Handles meeting web routes and Jinja template rendering

This module contains all meeting-related web routes for the CSA Platform, including:
- Meeting home page
- Meeting room pages
- WebSocket connections for real-time meeting interactions
"""
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
import logging
import json

from src.views.meeting.manager import MeetingManager

# Get logger
logger = logging.getLogger("fastapi")

# Create router for meeting web routes
router = APIRouter(
    prefix="/meeting",
    tags=["web-meeting"],
    responses={404: {"description": "Not found"}},
)

# Templates
templates = Jinja2Templates(directory="src/web/meeting/templates")

# Meeting manager instance
meeting_manager = MeetingManager()

@router.get("/")
async def meeting_home(request: Request):
    """Home page for meetings"""
    return templates.TemplateResponse(request=request, name="home.html")

@router.get("/room/{room_id}")
async def get_meeting_room(request: Request, room_id: str):
    """Get meeting room page"""
    # In a real application, you would fetch this data from a database
    meeting = {
        "id": room_id,
        "title": f"Meeting {room_id}",
        "description": "This is a description of the meeting. It includes agenda items and other relevant information.",
        "date_formatted": "May 1, 2025",
        "start_time": "10:00 AM",
        "end_time": "11:00 AM",
        "organizer": "John Smith",
        "notes": "Previous meeting notes will appear here."
    }
    
    participants = [
        {"name": "John Smith", "initials": "JS", "role": "Organizer", "is_speaking": True},
        {"name": "Jane Doe", "initials": "JD", "role": "Product Manager", "is_muted": False},
        {"name": "Bob Johnson", "initials": "BJ", "role": "Developer", "is_muted": True},
        {"name": "Alice Brown", "initials": "AB", "role": "Designer", "is_muted": False}
    ]
    
    return templates.TemplateResponse(
        request=request, 
        name="modern_meeting_room.html",
        context={
            "request": request, 
            "meeting": meeting, 
            "participants": participants
        }
    )

# WebSocket endpoint for meeting rooms
@router.websocket("/ws/{room_name}/{client_id}")
async def meeting_websocket_endpoint(websocket: WebSocket, room_name: str, client_id: str):
    """WebSocket endpoint for meeting rooms"""
    try:
        logger.info(f"Client {client_id} joining room {room_name}")
        await meeting_manager.join(room_name, client_id, websocket)
        
        while True:
            try:
                data = await websocket.receive_json()
                logger.info(f"Received message type: {data.get('type')} from client {client_id}")
                await meeting_manager.broadcast(room_name, data, client_id)
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from room {room_name}")
                await meeting_manager.leave(room_name, client_id)
                break
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        raise

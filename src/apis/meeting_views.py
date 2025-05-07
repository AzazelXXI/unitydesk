from fastapi import APIRouter, Depends, HTTPException, WebSocket
from src.controllers.meeting_controller import MeetingController
from src.schemas.meeting import MeetingCreate, MeetingUpdate

router = APIRouter(
    prefix="/api/meetings",
    tags=["meetings"],
    responses={404: {"description": "Not found"}},
)
controller = MeetingController()


@router.get("/")
async def get_meetings():
    """Get all meetings"""
    return controller.get_meetings()


@router.post("/", status_code=201)
async def create_meeting(meeting: MeetingCreate):
    """Create a new meeting"""
    return controller.create_meeting(meeting)


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: int):
    """Get meeting by ID"""
    meeting = controller.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.put("/{meeting_id}")
async def update_meeting(meeting_id: int, meeting: MeetingUpdate):
    """Update meeting"""
    updated_meeting = controller.update_meeting(meeting_id, meeting)
    if not updated_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return updated_meeting


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(meeting_id: int):
    """Delete meeting"""
    success = controller.delete_meeting(meeting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return None

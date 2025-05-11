from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from src.database import get_db
from src.controllers.calendar_controller import CalendarController
from src.schemas.calendar import (
    CalendarCreate, CalendarUpdate, CalendarRead,
    EventCreate, EventUpdate, EventRead,
    EventParticipantUpdate
)

# Configure router
router = APIRouter(
    tags=["calendars"],
    responses={404: {"description": "Not found"}}
)

# Calendar endpoints
@router.post("/calendars", response_model=CalendarRead, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    calendar_data: CalendarCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new calendar
    """
    return await CalendarController.create_calendar(calendar_data, db)


@router.get("/calendars", response_model=List[CalendarRead])
async def get_calendars(
    user_id: int = Query(..., description="ID of the user to get calendars for"),
    include_public: bool = Query(True, description="Whether to include public calendars"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all calendars for a user, including their own and optionally public ones
    """
    return await CalendarController.get_calendars(user_id, include_public, db)


@router.get("/calendars/{calendar_id}", response_model=CalendarRead)
async def get_calendar(
    calendar_id: int,
    user_id: int = Query(..., description="ID of the user accessing the calendar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific calendar by ID if the user has access
    """
    return await CalendarController.get_calendar(calendar_id, user_id, db)


@router.put("/calendars/{calendar_id}", response_model=CalendarRead)
async def update_calendar(
    calendar_id: int,
    calendar_data: CalendarUpdate,
    user_id: int = Query(..., description="ID of the user updating the calendar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing calendar
    """
    return await CalendarController.update_calendar(calendar_id, calendar_data, user_id, db)


@router.delete("/calendars/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    calendar_id: int,
    user_id: int = Query(..., description="ID of the user deleting the calendar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a calendar
    """
    await CalendarController.delete_calendar(calendar_id, user_id, db)
    return None


# Event endpoints
@router.post("/calendars/{calendar_id}/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    calendar_id: int,
    event_data: EventCreate,
    user_id: int = Query(..., description="ID of the user creating the event"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new event in a calendar
    """
    return await CalendarController.create_event(calendar_id, event_data, user_id, db)


@router.get("/calendars/{calendar_id}/events", response_model=List[EventRead])
async def get_calendar_events(
    calendar_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter events starting from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events ending before this date"),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Query(None, description="ID of the user accessing events (for filtering)")
):
    """
    Get all events in a calendar within a date range
    """
    return await CalendarController.get_events(calendar_id, db, start_date, end_date, user_id)


@router.get("/events/{event_id}", response_model=EventRead)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific event by ID
    """
    return await CalendarController.get_event(event_id, db)


@router.put("/events/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    user_id: int = Query(..., description="ID of the user updating the event"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing event
    """
    return await CalendarController.update_event(event_id, event_data, user_id, db)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    user_id: int = Query(..., description="ID of the user deleting the event"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an event
    """
    await CalendarController.delete_event(event_id, user_id, db)
    return None


@router.patch("/events/{event_id}/response", status_code=status.HTTP_200_OK)
async def update_participant_response(
    event_id: int,
    status_data: EventParticipantUpdate,
    user_id: int = Query(..., description="ID of the user responding to the event"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a participant's response status for an event
    """
    return await CalendarController.update_participant_status(event_id, user_id, status_data, db)

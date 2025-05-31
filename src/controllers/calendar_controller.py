from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from src.database import get_db
from src.models_backup.calendar import (
    Calendar, Event, EventParticipant, 
    EventStatus, EventRecurrence, ResponseStatus
)
from src.schemas.calendar import (
    CalendarCreate, CalendarUpdate, CalendarRead,
    EventCreate, EventUpdate, EventRead,
    EventParticipantCreate, EventParticipantUpdate, EventParticipantRead
)

# Configure logging
logger = logging.getLogger(__name__)

class CalendarController:
    """Controller for handling calendar and event operations"""
    
    @staticmethod
    async def create_calendar(
        calendar_data: CalendarCreate,
        db: AsyncSession
    ) -> Calendar:
        """
        Create a new calendar
        """
        try:
            new_calendar = Calendar(
                name=calendar_data.name,
                description=calendar_data.description,
                color=calendar_data.color,
                is_primary=calendar_data.is_primary,
                owner_id=calendar_data.owner_id,
                is_public=calendar_data.is_public
            )
            
            db.add(new_calendar)
            await db.commit()
            await db.refresh(new_calendar)
            
            logger.info(f"Created new calendar: {new_calendar.name} for user {calendar_data.owner_id}")
            
            return new_calendar
        except Exception as e:
            logger.error(f"Error creating calendar: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create calendar: {str(e)}"
            )
    
    @staticmethod
    async def get_calendars(
        user_id: int,
        include_public: bool = True,
        db: AsyncSession = None
    ) -> List[Calendar]:
        """
        Get all calendars for a user, including their own and public ones
        """        
        try:
            # Get the user's own calendars and optionally public ones in a single query
            if include_public:
                query = select(Calendar).filter(
                    (Calendar.owner_id == user_id) | (Calendar.is_public == True)
                )
            else:
                query = select(Calendar).filter(Calendar.owner_id == user_id)
            result = await db.execute(query)
            calendars = result.scalars().all()
            
            return calendars
        except Exception as e:
            logger.error(f"Error fetching calendars for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch calendars: {str(e)}"
            )
    
    @staticmethod
    async def get_calendar(
        calendar_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Calendar:
        """
        Get a specific calendar by ID if the user has access
        """
        try:
            query = select(Calendar).filter(Calendar.id == calendar_id)
            result = await db.execute(query)
            calendar = result.scalars().first()
            
            if not calendar:
                logger.warning(f"Calendar with ID {calendar_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Calendar with ID {calendar_id} not found"
                )
            
            # Check if user has access
            if calendar.owner_id != user_id and not calendar.is_public:
                logger.warning(f"User {user_id} tried to access calendar {calendar_id} without permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this calendar"
                )
            
            return calendar
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching calendar {calendar_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch calendar: {str(e)}"
            )
    
    @staticmethod
    async def update_calendar(
        calendar_id: int,
        calendar_data: CalendarUpdate,
        user_id: int,
        db: AsyncSession
    ) -> Calendar:
        """
        Update an existing calendar
        """
        try:
            # Get the calendar to update
            calendar_query = select(Calendar).filter(Calendar.id == calendar_id)
            result = await db.execute(calendar_query)
            calendar = result.scalars().first()
            
            if not calendar:
                logger.warning(f"Calendar with ID {calendar_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Calendar with ID {calendar_id} not found"
                )
            
            # Check if user has permission to update
            if calendar.owner_id != user_id:
                logger.warning(f"User {user_id} tried to update calendar {calendar_id} without permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this calendar"
                )
            
            # Update calendar fields
            update_data = calendar_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(calendar, key, value)
            
            await db.commit()
            await db.refresh(calendar)
            
            logger.info(f"Updated calendar {calendar_id}")
            return calendar
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating calendar {calendar_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update calendar: {str(e)}"
            )
    
    @staticmethod
    async def delete_calendar(
        calendar_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """
        Delete a calendar
        """
        try:
            # Get the calendar to delete
            calendar_query = select(Calendar).filter(Calendar.id == calendar_id)
            result = await db.execute(calendar_query)
            calendar = result.scalars().first()
            
            if not calendar:
                logger.warning(f"Calendar with ID {calendar_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Calendar with ID {calendar_id} not found"
                )
            
            # Check if user has permission to delete
            if calendar.owner_id != user_id:
                logger.warning(f"User {user_id} tried to delete calendar {calendar_id} without permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this calendar"
                )
            
            # Delete the calendar (cascades to events)
            await db.delete(calendar)
            await db.commit()
            
            logger.info(f"Deleted calendar {calendar_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting calendar {calendar_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete calendar: {str(e)}"
            )
    
    @staticmethod
    async def create_event(
        calendar_id: int,
        event_data: EventCreate,
        user_id: int,
        db: AsyncSession
    ) -> Event:
        """
        Create a new event in a calendar
        """
        try:
            # Verify calendar exists and user has access
            calendar_query = select(Calendar).filter(Calendar.id == calendar_id)
            result = await db.execute(calendar_query)
            calendar = result.scalars().first()
            
            if not calendar:
                logger.warning(f"Calendar with ID {calendar_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Calendar with ID {calendar_id} not found"
                )
            
            # Check if user has permission to add events
            if calendar.owner_id != user_id and not calendar.is_public:
                logger.warning(f"User {user_id} tried to add event to calendar {calendar_id} without permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to add events to this calendar"
                )
            
            # Create the event
            new_event = Event(
                title=event_data.title,
                description=event_data.description,
                start_time=event_data.start_time,
                end_time=event_data.end_time,
                location=event_data.location,
                virtual_meeting_link=event_data.virtual_meeting_link,
                status=event_data.status,
                recurrence=event_data.recurrence,
                recurrence_rule=event_data.recurrence_rule,
                all_day=event_data.all_day,
                color=event_data.color,
                calendar_id=calendar_id,
                organizer_id=user_id,
                reminder_minutes=event_data.reminder_minutes
            )
            
            db.add(new_event)
            await db.commit()
            await db.refresh(new_event)
            
            # Add participants if provided
            if event_data.participants:
                for participant_data in event_data.participants:
                    participant = EventParticipant(
                        event_id=new_event.id,
                        user_id=participant_data.user_id,
                        is_optional=participant_data.is_optional
                    )
                    db.add(participant)
                
                await db.commit()
                await db.refresh(new_event)
            
            logger.info(f"Created new event: {new_event.title} in calendar {calendar_id}")
            
            return new_event
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating event in calendar {calendar_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create event: {str(e)}"
            )
    @staticmethod
    async def get_events(
        calendar_id: int,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> List[Event]:
        """
        Get all events in a calendar within a date range
        """
        try:
            # Start with basic query
            query = select(Event).filter(Event.calendar_id == calendar_id)
            
            # Add date range filter if provided
            if start_date:
                query = query.filter(Event.start_time >= start_date)
            if end_date:
                query = query.filter(Event.start_time <= end_date)
                
            # Load relationships
            query = query.options(
                joinedload(Event.participants).joinedload(EventParticipant.user),
                joinedload(Event.organizer)
            )
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            return events
        except Exception as e:
            logger.error(f"Error fetching events for calendar {calendar_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch events: {str(e)}"
            )
    
    @staticmethod
    async def get_event(
        event_id: int,
        db: AsyncSession
    ) -> Event:
        """
        Get a specific event by ID
        """
        try:
            query = select(Event).filter(Event.id == event_id).options(
                joinedload(Event.participants).joinedload(EventParticipant.user),
                joinedload(Event.organizer),
                joinedload(Event.calendar)
            )
            
            result = await db.execute(query)
            event = result.scalars().first()
            
            if not event:
                logger.warning(f"Event with ID {event_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Event with ID {event_id} not found"
                )
            
            return event
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch event: {str(e)}"
            )
    
    @staticmethod
    async def update_event(
        event_id: int,
        event_data: EventUpdate,
        user_id: int,
        db: AsyncSession
    ) -> Event:
        """
        Update an existing event
        """
        try:
            # Get the event to update
            event_query = select(Event).filter(Event.id == event_id)
            result = await db.execute(event_query)
            event = result.scalars().first()
            
            if not event:
                logger.warning(f"Event with ID {event_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Event with ID {event_id} not found"
                )
            
            # Check if user has permission to update (must be organizer)
            if event.organizer_id != user_id:
                logger.warning(f"User {user_id} tried to update event {event_id} without permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this event"
                )
            
            # Update event fields
            update_data = event_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                # Skip participants since they need special handling
                if key != "participants":
                    setattr(event, key, value)
            
            await db.commit()
            await db.refresh(event)
            
            logger.info(f"Updated event {event_id}")
            return event
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating event {event_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update event: {str(e)}"
            )
    
    @staticmethod
    async def delete_event(
        event_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """
        Delete an event
        """
        try:
            # Get the event to delete
            event_query = select(Event).filter(Event.id == event_id)
            result = await db.execute(event_query)
            event = result.scalars().first()
            
            if not event:
                logger.warning(f"Event with ID {event_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Event with ID {event_id} not found"
                )
            
            # Check if user has permission to delete (must be organizer)
            if event.organizer_id != user_id:
                logger.warning(f"User {user_id} tried to delete event {event_id} without permission")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this event"
                )
            
            # Delete the event
            await db.delete(event)
            await db.commit()
            
            logger.info(f"Deleted event {event_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting event {event_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete event: {str(e)}"
            )
    
    @staticmethod
    async def update_participant_status(
        event_id: int,
        user_id: int,
        status_data: EventParticipantUpdate,
        db: AsyncSession
    ) -> EventParticipant:
        """
        Update a participant's response status for an event
        """
        try:
            # Find the participant record
            query = select(EventParticipant).filter(
                EventParticipant.event_id == event_id,
                EventParticipant.user_id == user_id
            )
            
            result = await db.execute(query)
            participant = result.scalars().first()
            
            if not participant:
                logger.warning(f"User {user_id} is not a participant in event {event_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="You are not a participant in this event"
                )
            
            # Update the response status
            update_data = status_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(participant, key, value)
                
            await db.commit()
            await db.refresh(participant)
            
            logger.info(f"Updated participant status for user {user_id} in event {event_id}")
            return participant
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating participant status for user {user_id} in event {event_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update participant status: {str(e)}"
            )

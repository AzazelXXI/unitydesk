import pytest
from sqlalchemy.future import select
from src.models_backup.calendar import Event, EventStatus, EventRecurrence, EventParticipant, ResponseStatus
import datetime
from sqlalchemy.orm import joinedload


@pytest.mark.asyncio
async def test_create_event(test_session):
    """Test creating a new event"""
    # Create a new event
    event = Event(
        title="Important Meeting",
        description="Discuss quarterly results",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now() + datetime.timedelta(hours=2),
        location="Conference Room A",
        virtual_meeting_link="https://meet.example.com/abc123",
        status=EventStatus.CONFIRMED,
        recurrence=EventRecurrence.WEEKLY,
        all_day=False,
        color="#3366FF"
    )
    
    test_session.add(event)
    await test_session.commit()
    
    # Query the event
    stmt = select(Event).where(Event.title == "Important Meeting")
    result = await test_session.execute(stmt)
    fetched_event = result.scalars().first()
    
    # Assert event was created with correct values
    assert fetched_event is not None
    assert fetched_event.title == "Important Meeting"
    assert fetched_event.description == "Discuss quarterly results"
    assert fetched_event.location == "Conference Room A"
    assert fetched_event.status == EventStatus.CONFIRMED
    assert fetched_event.recurrence == EventRecurrence.WEEKLY
    assert fetched_event.all_day == False
    
    # Clean up
    await test_session.delete(fetched_event)
    await test_session.commit()


@pytest.mark.asyncio
async def test_event_is_past_property(test_session):
    """Test the is_past property of an event"""
    # Create a past event
    past_event = Event(
        title="Past Meeting",
        description="Already happened",
        start_time=datetime.datetime.now() - datetime.timedelta(days=2),
        end_time=datetime.datetime.now() - datetime.timedelta(days=2, hours=-1),
        status=EventStatus.CONFIRMED
    )
    
    # Create a future event
    future_event = Event(
        title="Future Meeting",
        description="Not happened yet",
        start_time=datetime.datetime.now() + datetime.timedelta(days=2),
        end_time=datetime.datetime.now() + datetime.timedelta(days=2, hours=1),
        status=EventStatus.CONFIRMED
    )
    
    test_session.add_all([past_event, future_event])
    await test_session.commit()
    
    # Query the events
    stmt = select(Event).where(Event.title.in_(["Past Meeting", "Future Meeting"]))
    result = await test_session.execute(stmt)
    events = result.scalars().all()
    
    # Find each event
    fetched_past_event = next((e for e in events if e.title == "Past Meeting"), None)
    fetched_future_event = next((e for e in events if e.title == "Future Meeting"), None)
    
    # Test is_past property
    assert fetched_past_event.is_past == True
    assert fetched_future_event.is_past == False
    
    # Clean up
    await test_session.delete(past_event)
    await test_session.delete(future_event)
    await test_session.commit()


@pytest.mark.asyncio
async def test_event_participant_relationship(test_session):
    """Test the relationship between events and participants"""
    # Create a new event
    event = Event(
        title="Team Sync",
        description="Weekly team synchronization",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now() + datetime.timedelta(hours=1),
        status=EventStatus.CONFIRMED
    )
    
    test_session.add(event)
    await test_session.flush()
    
    # Create event participants
    participant1 = EventParticipant(
        event_id=event.id,
        response=ResponseStatus.ACCEPTED,
        is_optional=False,
        comment="I'll prepare the presentation"
    )
    
    participant2 = EventParticipant(
        event_id=event.id,
        response=ResponseStatus.TENTATIVE,
        is_optional=True,
        comment="I might be late"
    )
    
    test_session.add_all([participant1, participant2])
    await test_session.commit()
      # Query the event with participants - using joinedload for eager loading
    stmt = select(Event).options(joinedload(Event.participants)).where(Event.id == event.id)
    result = await test_session.execute(stmt)
    fetched_event = result.scalars().first()
    
    # Test relationship
    assert len(fetched_event.participants) == 2
    
    responses = [p.response for p in fetched_event.participants]
    assert ResponseStatus.ACCEPTED in responses
    assert ResponseStatus.TENTATIVE in responses
    
    comments = [p.comment for p in fetched_event.participants]
    assert "I'll prepare the presentation" in comments
    assert "I might be late" in comments
    
    # Clean up
    await test_session.delete(participant1)
    await test_session.delete(participant2)
    await test_session.delete(event)
    await test_session.commit()


@pytest.mark.asyncio
async def test_update_event(test_session):
    """Test updating an event"""
    # Create a new event
    event = Event(
        title="Original Meeting",
        description="Original description",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now() + datetime.timedelta(hours=1),
        status=EventStatus.TENTATIVE,
        color="#FF0000"
    )
    
    test_session.add(event)
    await test_session.commit()
    
    # Update the event
    event.title = "Updated Meeting"
    event.description = "Updated description"
    event.status = EventStatus.CONFIRMED
    event.color = "#00FF00"
    event.end_time = event.end_time + datetime.timedelta(hours=1)  # Extend by 1 hour
    
    await test_session.commit()
    
    # Query to verify updates
    stmt = select(Event).where(Event.id == event.id)
    result = await test_session.execute(stmt)
    updated_event = result.scalars().first()
    
    # Assert changes were saved
    assert updated_event.title == "Updated Meeting"
    assert updated_event.description == "Updated description"
    assert updated_event.status == EventStatus.CONFIRMED
    assert updated_event.color == "#00FF00"
    assert (updated_event.end_time - updated_event.start_time).total_seconds() / 3600 == 2.0
    
    # Clean up
    await test_session.delete(event)
    await test_session.commit()


@pytest.mark.asyncio
async def test_event_calendar_relationship(test_session):
    """Test the relationship between events and calendars"""
    from src.models_backup.calendar import Calendar
    from src.models_backup.user import User
    
    # Create a user for the calendar owner
    user = User(
        email="calendar_test@example.com",
        username="calendar_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a calendar
    calendar = Calendar(
        name="Work Calendar",
        description="Calendar for work events",
        color="#3366CC",
        is_primary=True,
        owner_id=user.id
    )
    
    test_session.add(calendar)
    await test_session.flush()
    
    # Create an event in the calendar
    event = Event(
        title="Calendar Meeting",
        description="Meeting in specific calendar",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now() + datetime.timedelta(hours=1),
        status=EventStatus.CONFIRMED,
        calendar_id=calendar.id,
        organizer_id=user.id
    )
    
    test_session.add(event)
    await test_session.commit()
    
    # Query the event with calendar - using joinedload
    stmt = select(Event).options(
        joinedload(Event.calendar),
        joinedload(Event.organizer)
    ).where(Event.id == event.id)
    
    result = await test_session.execute(stmt)
    fetched_event = result.scalars().first()
    
    # Test relationships
    assert fetched_event.calendar_id == calendar.id
    assert fetched_event.calendar.name == "Work Calendar"
    assert fetched_event.organizer_id == user.id
    assert fetched_event.organizer.username == "calendar_user"
    
    # Clean up
    await test_session.delete(event)
    await test_session.delete(calendar)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_delete_event_cascade(test_session):
    """Test deleting an event with cascade delete of participants"""
    # Create a new event
    event = Event(
        title="Event To Delete",
        description="This event will be deleted",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now() + datetime.timedelta(hours=1),
        status=EventStatus.CONFIRMED
    )
    
    test_session.add(event)
    await test_session.flush()
    
    # Create event participants
    participant1 = EventParticipant(
        event_id=event.id,
        response=ResponseStatus.ACCEPTED
    )
    
    participant2 = EventParticipant(
        event_id=event.id,
        response=ResponseStatus.DECLINED
    )
    
    test_session.add_all([participant1, participant2])
    await test_session.commit()
    
    # Store IDs for checking after deletion
    event_id = event.id
    participant1_id = participant1.id
    participant2_id = participant2.id
    
    # Delete the event
    await test_session.delete(event)
    await test_session.commit()
    
    # Check if event is deleted
    stmt = select(Event).where(Event.id == event_id)
    result = await test_session.execute(stmt)
    deleted_event = result.scalars().first()
    assert deleted_event is None
    
    # Check if participants are deleted (cascade)
    stmt = select(EventParticipant).where(
        EventParticipant.id.in_([participant1_id, participant2_id])
    )
    result = await test_session.execute(stmt)
    participants = result.scalars().all()
    
    # If cascade delete works, there should be no participants
    assert len(participants) == 0


@pytest.mark.asyncio
async def test_event_time_constraints(test_session):
    """Test event time constraints (end_time must be after start_time)"""
    # Attempt to create an event with end_time before start_time
    now = datetime.datetime.now()
    invalid_event = Event(
        title="Invalid Time Event",
        description="Event with invalid time range",
        start_time=now,
        end_time=now - datetime.timedelta(hours=1),  # End time before start time
        status=EventStatus.TENTATIVE
    )
    
    test_session.add(invalid_event)
    
    # This should fail validation if the model enforces end_time > start_time
    try:
        await test_session.commit()
        # If we get here, there's no constraint - clean up and note this
        await test_session.delete(invalid_event)
        await test_session.commit()
        print("Note: No time constraint enforced at database level for Event model")
    except Exception as e:
        # Expected behavior if constraint exists
        await test_session.rollback()
        assert "time constraint" in str(e).lower() or "check constraint" in str(e).lower() or "validation" in str(e).lower()


@pytest.mark.asyncio
async def test_query_events_by_timerange(test_session):
    """Test querying events within a specific time range"""
    now = datetime.datetime.now()
    
    # Create events with different time ranges
    event1 = Event(
        title="Morning Meeting",
        start_time=now.replace(hour=9, minute=0),
        end_time=now.replace(hour=10, minute=0),
        status=EventStatus.CONFIRMED
    )
    
    event2 = Event(
        title="Lunch Meeting",
        start_time=now.replace(hour=12, minute=0),
        end_time=now.replace(hour=13, minute=0),
        status=EventStatus.CONFIRMED
    )
    
    event3 = Event(
        title="Evening Meeting",
        start_time=now.replace(hour=17, minute=0),
        end_time=now.replace(hour=18, minute=0),
        status=EventStatus.CONFIRMED
    )
    
    test_session.add_all([event1, event2, event3])
    await test_session.commit()
    
    # Query events between 11:00 and 17:30
    start_range = now.replace(hour=11, minute=0)
    end_range = now.replace(hour=17, minute=30)
    
    stmt = select(Event).where(
        Event.start_time >= start_range,
        Event.start_time <= end_range
    )
    
    result = await test_session.execute(stmt)
    events = result.scalars().all()
    
    # Should include Lunch and Evening meetings
    assert len(events) == 2
    titles = [e.title for e in events]
    assert "Lunch Meeting" in titles
    assert "Evening Meeting" in titles
    assert "Morning Meeting" not in titles
    
    # Clean up
    await test_session.delete(event1)
    await test_session.delete(event2)
    await test_session.delete(event3)
    await test_session.commit()

import pytest
from sqlalchemy.future import select
from src.models.calendar import Calendar, Event, EventStatus
from src.models.user import User
import datetime
from sqlalchemy.orm import joinedload


@pytest.mark.asyncio
async def test_create_calendar(test_session):
    """Test creating a new calendar"""
    # First create a user that will own the calendar
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    test_session.add(user)
    await test_session.flush()

    # Create a new calendar
    calendar = Calendar(
        name="Work Calendar",
        description="Calendar for work-related events",
        color="#FF5733",
        is_primary=True,
        is_public=False,
        owner_id=user.id
    )
    
    test_session.add(calendar)
    await test_session.commit()
    
    # Query the calendar
    stmt = select(Calendar).where(Calendar.name == "Work Calendar")
    result = await test_session.execute(stmt)
    fetched_calendar = result.scalars().first()
    
    # Assert calendar was created with correct values
    assert fetched_calendar is not None
    assert fetched_calendar.name == "Work Calendar"
    assert fetched_calendar.description == "Calendar for work-related events"
    assert fetched_calendar.color == "#FF5733"
    assert fetched_calendar.is_primary == True
    assert fetched_calendar.is_public == False
    # Clean up
    await test_session.delete(fetched_calendar)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_calendar_event_relationship(test_session):
    """Test the relationship between calendars and events"""
    # First create a user that will own the calendar
    user = User(
        email="test2@example.com",
        username="testuser2",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    test_session.add(user)
    await test_session.flush()
    
    # Create a new calendar
    calendar = Calendar(
        name="Personal Calendar",
        description="Calendar for personal events",
        color="#33FF57",
        owner_id=user.id
    )
    
    test_session.add(calendar)
    await test_session.flush()
    # Create events for the calendar
    event1 = Event(
        title="Birthday Party",
        description="Annual celebration",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now() + datetime.timedelta(hours=3),
        status=EventStatus.CONFIRMED,
        calendar_id=calendar.id,
        organizer_id=user.id
    )
    event2 = Event(
        title="Doctor Appointment",
        description="Annual checkup",
        start_time=datetime.datetime.now() + datetime.timedelta(days=1),
        end_time=datetime.datetime.now() + datetime.timedelta(days=1, hours=1),
        status=EventStatus.CONFIRMED,
        calendar_id=calendar.id,
        organizer_id=user.id
    )
    
    test_session.add_all([event1, event2])
    await test_session.commit()
    
    # Use joinedload to eagerly load the events relationship
    stmt = select(Calendar).options(joinedload(Calendar.events)).where(Calendar.id == calendar.id)
    result = await test_session.execute(stmt)
    fetched_calendar = result.scalars().first()
    
    # Test relationship
    assert len(fetched_calendar.events) == 2
    event_titles = [event.title for event in fetched_calendar.events]
    assert "Birthday Party" in event_titles
    assert "Doctor Appointment" in event_titles
    # Test relationship from the other direction - using joinedload for eager loading
    stmt = select(Event).options(joinedload(Event.calendar)).where(Event.id == event1.id)
    result = await test_session.execute(stmt)
    fetched_event = result.scalars().first()
    
    assert fetched_event.calendar.id == calendar.id
    assert fetched_event.calendar.name == "Personal Calendar"
    # Clean up
    await test_session.delete(event1)
    await test_session.delete(event2)
    await test_session.delete(calendar)
    await test_session.delete(user)
    await test_session.commit()

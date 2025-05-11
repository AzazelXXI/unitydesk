import pytest
from sqlalchemy.future import select
from src.models.calendar import Event, EventStatus, EventRecurrence, EventParticipant, ResponseStatus
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

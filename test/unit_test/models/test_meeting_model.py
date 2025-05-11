import pytest
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import uuid

from src.models.meeting import Meeting, Participant, MeetingStatus
from src.models.user import User, UserRole

@pytest.mark.asyncio
async def test_create_meeting(test_session):
    """Test creating a new meeting"""
    # Create host user
    host = User(
        email="host_user@example.com",
        username="host_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True,
        role=UserRole.MANAGER
    )
    
    test_session.add(host)
    await test_session.flush()
    
    # Create meeting
    meeting = Meeting(
        room_name=f"test-meeting-{uuid.uuid4().hex[:8]}",  # Ensure unique room name
        host_id=host.id,
        description="Test meeting for unit testing",
        status=MeetingStatus.SCHEDULED,
        is_recurring=False,
        scheduled_start_time=datetime.utcnow() + timedelta(hours=1),
        scheduled_end_time=datetime.utcnow() + timedelta(hours=2)
    )
    
    test_session.add(meeting)
    await test_session.commit()
    
    # Query the meeting with eager loading of host relationship
    stmt = select(Meeting).options(joinedload(Meeting.host)).where(Meeting.id == meeting.id)
    result = await test_session.execute(stmt)
    fetched_meeting = result.scalars().first()
    
    # Assert meeting was created with correct values
    assert fetched_meeting is not None
    assert fetched_meeting.room_name == meeting.room_name
    assert fetched_meeting.status == MeetingStatus.SCHEDULED
    assert fetched_meeting.host.username == "host_user"
    assert fetched_meeting.is_recurring == False
    assert fetched_meeting.scheduled_start_time is not None
    assert fetched_meeting.scheduled_end_time is not None
    assert fetched_meeting.actual_start_time is None  # Should be None initially
    
    # Clean up
    await test_session.delete(meeting)
    await test_session.delete(host)
    await test_session.commit()

@pytest.mark.asyncio
async def test_update_meeting_status(test_session):
    """Test updating meeting status"""
    # Create host user
    host = User(
        email="status_test@example.com",
        username="status_test",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(host)
    await test_session.flush()
    
    # Create meeting
    meeting = Meeting(
        room_name=f"status-test-{uuid.uuid4().hex[:8]}",
        host_id=host.id,
        status=MeetingStatus.SCHEDULED,
        description="Meeting to test status changes",
        scheduled_start_time=datetime.utcnow(),
        scheduled_end_time=datetime.utcnow() + timedelta(hours=1)
    )
    
    test_session.add(meeting)
    await test_session.flush()
    
    # Update meeting to in progress
    meeting.status = MeetingStatus.IN_PROGRESS
    meeting.actual_start_time = datetime.utcnow()
    await test_session.commit()
    
    # Query the updated meeting
    stmt = select(Meeting).where(Meeting.id == meeting.id)
    result = await test_session.execute(stmt)
    fetched_meeting = result.scalars().first()
    
    # Check if status was updated
    assert fetched_meeting.status == MeetingStatus.IN_PROGRESS
    assert fetched_meeting.actual_start_time is not None
    
    # Update meeting to completed
    fetched_meeting.status = MeetingStatus.COMPLETED
    fetched_meeting.actual_end_time = datetime.utcnow()
    await test_session.commit()
    
    # Query the meeting again
    result = await test_session.execute(stmt)
    completed_meeting = result.scalars().first()
    
    # Check if status was updated to completed
    assert completed_meeting.status == MeetingStatus.COMPLETED
    assert completed_meeting.actual_end_time is not None
    
    # Clean up
    await test_session.delete(meeting)
    await test_session.delete(host)
    await test_session.commit()

@pytest.mark.asyncio
async def test_meeting_participants(test_session):
    """Test adding participants to a meeting"""
    # Create host and participant users
    host = User(
        email="meeting_host@example.com",
        username="meeting_host",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    user_participant = User(
        email="user_participant@example.com",
        username="user_participant",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([host, user_participant])
    await test_session.flush()
    
    # Create meeting
    meeting = Meeting(
        room_name=f"participant-test-{uuid.uuid4().hex[:8]}",
        host_id=host.id,
        status=MeetingStatus.SCHEDULED,
        description="Meeting to test participants",
        scheduled_start_time=datetime.utcnow() + timedelta(minutes=30),
        scheduled_end_time=datetime.utcnow() + timedelta(hours=1, minutes=30)
    )
    
    test_session.add(meeting)
    await test_session.flush()
    
    # Add participants - one registered user and one guest
    participant1 = Participant(
        meeting_id=meeting.id,
        user_id=user_participant.id,
        client_id=f"client-{uuid.uuid4().hex[:10]}",
        joined_at=datetime.utcnow(),
        is_camera_on=True,
        is_mic_on=True
    )
    
    participant2 = Participant(
        meeting_id=meeting.id,
        name="Guest User",
        client_id=f"client-{uuid.uuid4().hex[:10]}",
        joined_at=datetime.utcnow(),
        is_camera_on=False,
        is_mic_on=True
    )
    
    test_session.add_all([participant1, participant2])
    await test_session.commit()
    
    # Query the meeting with eager loading of participants
    stmt = select(Meeting).options(
        joinedload(Meeting.participants).joinedload(Participant.user)
    ).where(Meeting.id == meeting.id)
    
    result = await test_session.execute(stmt)
    fetched_meeting = result.scalars().first()
    
    # Check participants
    assert fetched_meeting is not None
    assert len(fetched_meeting.participants) == 2
    
    # Check participant details
    participants = {p.client_id: p for p in fetched_meeting.participants}
    registered_participant = next((p for p in fetched_meeting.participants if p.user_id is not None), None)
    guest_participant = next((p for p in fetched_meeting.participants if p.user_id is None), None)
    
    assert registered_participant is not None
    assert guest_participant is not None
    
    assert registered_participant.user.username == "user_participant"
    assert registered_participant.name is None  # Name not set as it uses the user account
    assert guest_participant.name == "Guest User"
    assert guest_participant.user_id is None
    
    # Update participant status
    registered_participant.is_screen_sharing = True
    await test_session.commit()
    
    # Check if participant was updated
    stmt = select(Participant).where(Participant.id == registered_participant.id)
    result = await test_session.execute(stmt)
    updated_participant = result.scalars().first()
    
    assert updated_participant.is_screen_sharing == True
    
    # Clean up
    await test_session.delete(meeting)  # Should cascade delete participants
    await test_session.delete(host)
    await test_session.delete(user_participant)
    await test_session.commit()

@pytest.mark.asyncio
async def test_cancel_meeting(test_session):
    """Test cancelling a meeting"""
    # Create host user
    host = User(
        email="cancel_test@example.com",
        username="cancel_test",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(host)
    await test_session.flush()
    
    # Create meeting
    meeting = Meeting(
        room_name=f"cancel-test-{uuid.uuid4().hex[:8]}",
        host_id=host.id,
        status=MeetingStatus.SCHEDULED,
        description="Meeting to test cancellation",
        scheduled_start_time=datetime.utcnow() + timedelta(days=1),
        scheduled_end_time=datetime.utcnow() + timedelta(days=1, hours=1)
    )
    
    test_session.add(meeting)
    await test_session.commit()
    
    # Cancel the meeting
    meeting.status = MeetingStatus.CANCELLED
    await test_session.commit()
    
    # Query the cancelled meeting
    stmt = select(Meeting).where(Meeting.id == meeting.id)
    result = await test_session.execute(stmt)
    fetched_meeting = result.scalars().first()
    
    # Check if status was updated to cancelled
    assert fetched_meeting.status == MeetingStatus.CANCELLED
    
    # Clean up
    await test_session.delete(meeting)
    await test_session.delete(host)
    await test_session.commit()

@pytest.mark.asyncio
async def test_recursive_meetings(test_session):
    """Test creating a recurring meeting"""
    # Create host user
    host = User(
        email="recurring_host@example.com",
        username="recurring_host",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(host)
    await test_session.flush()
    
    # Create recurring meeting
    meeting = Meeting(
        room_name=f"recurring-test-{uuid.uuid4().hex[:8]}",
        host_id=host.id,
        status=MeetingStatus.SCHEDULED,
        description="Weekly team meeting",
        is_recurring=True,
        scheduled_start_time=datetime.utcnow() + timedelta(days=1),
        scheduled_end_time=datetime.utcnow() + timedelta(days=1, hours=1)
    )
    
    test_session.add(meeting)
    await test_session.commit()
    
    # Query the meeting
    stmt = select(Meeting).where(Meeting.id == meeting.id)
    result = await test_session.execute(stmt)
    fetched_meeting = result.scalars().first()
    
    # Check if meeting was created as recurring
    assert fetched_meeting.is_recurring == True
    
    # Clean up
    await test_session.delete(meeting)
    await test_session.delete(host)
    await test_session.commit()

@pytest.mark.asyncio
async def test_participant_join_leave_flow(test_session):
    """Test participant joining and leaving a meeting"""
    # Create host user and meeting
    host = User(
        email="flow_host@example.com",
        username="flow_host",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(host)
    await test_session.flush()
    
    meeting = Meeting(
        room_name=f"flow-test-{uuid.uuid4().hex[:8]}",
        host_id=host.id,
        status=MeetingStatus.IN_PROGRESS,
        description="Meeting to test join/leave flow",
        actual_start_time=datetime.utcnow(),
    )
    
    test_session.add(meeting)
    await test_session.flush()
    
    # Create a participant who joins the meeting
    participant = Participant(
        meeting_id=meeting.id,
        name="Flow Test User",
        client_id=f"client-{uuid.uuid4().hex[:10]}",
        joined_at=datetime.utcnow(),
        is_camera_on=True,
        is_mic_on=True
    )
    
    test_session.add(participant)
    await test_session.commit()
    
    # Query the participant
    stmt = select(Participant).where(Participant.id == participant.id)
    result = await test_session.execute(stmt)
    fetched_participant = result.scalars().first()
    
    # Check initial state
    assert fetched_participant.joined_at is not None
    assert fetched_participant.left_at is None
    
    # Participant leaves the meeting
    fetched_participant.left_at = datetime.utcnow()
    fetched_participant.is_camera_on = False
    fetched_participant.is_mic_on = False
    await test_session.commit()
    
    # Query the participant again
    result = await test_session.execute(stmt)
    updated_participant = result.scalars().first()
    
    # Check if left_at was set correctly
    assert updated_participant.left_at is not None
    assert updated_participant.is_camera_on == False
    assert updated_participant.is_mic_on == False
    
    # Participant rejoins the meeting
    new_join = Participant(
        meeting_id=meeting.id,
        name="Flow Test User",
        client_id=f"client-{uuid.uuid4().hex[:10]}", # New client ID for new session
        joined_at=datetime.utcnow(),
        is_camera_on=True,
        is_mic_on=False  # Different settings this time
    )
    
    test_session.add(new_join)
    await test_session.commit()
    
    # Check that we now have two participant records for the same meeting
    stmt = select(Participant).where(Participant.meeting_id == meeting.id)
    result = await test_session.execute(stmt)
    all_participants = result.scalars().all()
    
    assert len(all_participants) == 2
    assert all_participants[0].left_at is not None
    assert all_participants[1].left_at is None  # New session hasn't left yet
    
    # Clean up
    await test_session.delete(meeting)  # Should cascade delete participants
    await test_session.delete(host)
    await test_session.commit()

@pytest.mark.asyncio
async def test_complete_meeting_flow(test_session):
    """Test complete lifecycle of a meeting from scheduled to completed"""
    # Create host user
    host = User(
        email="lifecycle_host@example.com",
        username="lifecycle_host",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    # Create participant user
    participant_user = User(
        email="lifecycle_participant@example.com",
        username="lifecycle_participant",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([host, participant_user])
    await test_session.flush()
    
    # 1. Create scheduled meeting
    meeting = Meeting(
        room_name=f"lifecycle-test-{uuid.uuid4().hex[:8]}",
        host_id=host.id,
        status=MeetingStatus.SCHEDULED,
        description="Meeting lifecycle test",
        scheduled_start_time=datetime.utcnow(),
        scheduled_end_time=datetime.utcnow() + timedelta(hours=1)
    )
    
    test_session.add(meeting)
    await test_session.commit()
    
    # 2. Start the meeting
    meeting.status = MeetingStatus.IN_PROGRESS
    meeting.actual_start_time = datetime.utcnow()
    await test_session.commit()
    
    # 3. Add participants
    participant1 = Participant(
        meeting_id=meeting.id,
        user_id=participant_user.id,
        client_id=f"client-{uuid.uuid4().hex[:10]}",
        joined_at=datetime.utcnow(),
        is_camera_on=True,
        is_mic_on=True
    )
    
    participant2 = Participant(
        meeting_id=meeting.id,
        name="Guest Attendee",
        client_id=f"client-{uuid.uuid4().hex[:10]}",
        joined_at=datetime.utcnow() + timedelta(minutes=2),
        is_camera_on=False,
        is_mic_on=True
    )
    
    test_session.add_all([participant1, participant2])
    await test_session.commit()
    
    # 4. Participant toggles settings
    participant1.is_screen_sharing = True
    await test_session.commit()
    
    # 5. One participant leaves
    participant2.left_at = datetime.utcnow() + timedelta(minutes=30)
    await test_session.commit()
    
    # 6. Complete the meeting
    meeting.status = MeetingStatus.COMPLETED
    meeting.actual_end_time = datetime.utcnow() + timedelta(minutes=45)
    await test_session.commit()
    
    # 7. Set remaining participants as left
    participant1.left_at = datetime.utcnow() + timedelta(minutes=45)
    await test_session.commit()
    
    # Query the completed meeting with eager loading
    stmt = select(Meeting).options(
        joinedload(Meeting.participants).joinedload(Participant.user),
        joinedload(Meeting.host)
    ).where(Meeting.id == meeting.id)
    
    result = await test_session.execute(stmt)
    completed_meeting = result.scalars().first()
    
    # Verify the final state
    assert completed_meeting.status == MeetingStatus.COMPLETED
    assert completed_meeting.actual_start_time is not None
    assert completed_meeting.actual_end_time is not None
    assert len(completed_meeting.participants) == 2
    
    # Check that all participants have left
    for participant in completed_meeting.participants:
        assert participant.left_at is not None
    
    # Verify registered participant details
    registered = next((p for p in completed_meeting.participants if p.user_id is not None), None)
    assert registered.user.username == "lifecycle_participant"
    assert registered.is_screen_sharing == True
    
    # Clean up
    await test_session.delete(meeting)  # Should cascade delete participants 
    await test_session.delete(host)
    await test_session.delete(participant_user)
    await test_session.commit()

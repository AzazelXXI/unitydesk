import pytest
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime
import json

from src.models.notification import (
    Notification, NotificationSetting, NotificationTemplate,
    NotificationType, NotificationPriority, NotificationChannel
)
from src.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_notification(test_session):
    """Test creating a notification for a user"""
    # Create a user
    user = User(
        email="notification_test@example.com",
        username="notification_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a notification for the user
    notification = Notification(
        user_id=user.id,
        title="Test Notification",
        content="This is a test notification content.",
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL,
        resource_type="test",
        resource_id=1,
        data={"test_key": "test_value"},
        icon="bell-icon"
    )
    
    test_session.add(notification)
    await test_session.commit()
    
    # Query the notification
    stmt = select(Notification).where(Notification.id == notification.id)
    result = await test_session.execute(stmt)
    fetched_notification = result.scalars().first()
    
    # Assert notification was created with correct values
    assert fetched_notification is not None
    assert fetched_notification.user_id == user.id
    assert fetched_notification.title == "Test Notification"
    assert fetched_notification.content == "This is a test notification content."
    assert fetched_notification.notification_type == NotificationType.SYSTEM
    assert fetched_notification.priority == NotificationPriority.NORMAL
    assert fetched_notification.resource_type == "test"
    assert fetched_notification.resource_id == 1
    assert fetched_notification.data["test_key"] == "test_value"
    assert fetched_notification.icon == "bell-icon"
    assert fetched_notification.read_at is None  # Should be unread initially
    assert fetched_notification.created_at is not None
    
    # Test the relationship from User to Notification
    # Query the user with eager loading of notifications
    stmt = select(User).options(joinedload(User.notifications)).where(User.id == user.id)
    result = await test_session.execute(stmt)
    fetched_user = result.scalars().first()
    
    # Assert the user has the notification
    assert fetched_user is not None
    assert len(fetched_user.notifications) == 1
    assert fetched_user.notifications[0].id == notification.id
    assert fetched_user.notifications[0].title == "Test Notification"
    
    # Clean up
    await test_session.delete(notification)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_mark_notification_as_read(test_session):
    """Test marking a notification as read"""
    # Create a user
    user = User(
        email="read_test@example.com",
        username="read_test_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a notification
    notification = Notification(
        user_id=user.id,
        title="Read Test",
        content="Testing read status",
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL
    )
    
    test_session.add(notification)
    await test_session.flush()
    
    # Initially the notification should be unread
    assert notification.read_at is None
    
    # Mark notification as read
    notification.read_at = datetime.utcnow()
    await test_session.commit()
    
    # Query the notification
    stmt = select(Notification).where(Notification.id == notification.id)
    result = await test_session.execute(stmt)
    updated_notification = result.scalars().first()
    
    # Assert notification was marked as read
    assert updated_notification.read_at is not None
    
    # Clean up
    await test_session.delete(notification)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notification_delivery_status(test_session):
    """Test updating notification delivery status for different channels"""
    # Create a user
    user = User(
        email="delivery_test@example.com",
        username="delivery_test_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a notification
    notification = Notification(
        user_id=user.id,
        title="Delivery Test",
        content="Testing delivery status",
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.HIGH,
        # All delivery statuses are False by default
    )
    
    test_session.add(notification)
    await test_session.commit()
    
    # Initially all delivery statuses should be False
    assert notification.in_app_delivered == False
    assert notification.email_delivered == False
    assert notification.push_delivered == False
    assert notification.sms_delivered == False
    
    # Simulate delivery through different channels
    notification.in_app_delivered = True
    notification.email_delivered = True
    await test_session.commit()
    
    # Query the notification
    stmt = select(Notification).where(Notification.id == notification.id)
    result = await test_session.execute(stmt)
    updated_notification = result.scalars().first()
    
    # Assert delivery statuses were updated
    assert updated_notification.in_app_delivered == True
    assert updated_notification.email_delivered == True
    assert updated_notification.push_delivered == False
    assert updated_notification.sms_delivered == False
    
    # Update more delivery statuses
    updated_notification.push_delivered = True
    await test_session.commit()
    
    # Query again
    result = await test_session.execute(stmt)
    final_notification = result.scalars().first()
    
    # Assert push delivery status was updated
    assert final_notification.push_delivered == True
    
    # Clean up
    await test_session.delete(notification)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notification_settings(test_session):
    """Test creating and updating notification settings for a user"""
    # Create a user
    user = User(
        email="settings_test@example.com",
        username="settings_test_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create notification settings for different notification types
    # Thêm trường user để đảm bảo cả user_id và user đều được thiết lập
    system_settings = NotificationSetting(
        user_id=user.id,
        user=user.id,  # Lưu ý: user là Column(Integer) chứ không phải relationship
        notification_type=NotificationType.SYSTEM,
        in_app_enabled=True,
        email_enabled=False,
        push_enabled=False,
        sms_enabled=False,
        min_priority=NotificationPriority.NORMAL
    )
    
    task_settings = NotificationSetting(
        user_id=user.id,
        user=user.id,  # Thiết lập giá trị cho cột user
        notification_type=NotificationType.TASK,
        in_app_enabled=True,
        email_enabled=True,
        push_enabled=True,
        sms_enabled=False,
        min_priority=NotificationPriority.LOW
    )
    
    test_session.add_all([system_settings, task_settings])
    await test_session.commit()
    
    # Query the settings
    stmt = select(NotificationSetting).where(
        NotificationSetting.user_id == user.id,
        NotificationSetting.notification_type == NotificationType.SYSTEM
    )
    result = await test_session.execute(stmt)
    fetched_system_settings = result.scalars().first()
    
    # Assert settings were created correctly
    assert fetched_system_settings is not None
    assert fetched_system_settings.in_app_enabled == True
    assert fetched_system_settings.email_enabled == False
    assert fetched_system_settings.min_priority == NotificationPriority.NORMAL
    
    # Update settings
    fetched_system_settings.email_enabled = True
    fetched_system_settings.min_priority = NotificationPriority.HIGH
    await test_session.commit()
    
    # Query again
    result = await test_session.execute(stmt)
    updated_settings = result.scalars().first()
    
    # Assert settings were updated
    assert updated_settings.email_enabled == True
    assert updated_settings.min_priority == NotificationPriority.HIGH
    
    # Query all settings for this user
    stmt = select(NotificationSetting).where(NotificationSetting.user_id == user.id)
    result = await test_session.execute(stmt)
    all_settings = result.scalars().all()
    
    # Should have settings for two notification types
    assert len(all_settings) == 2
    
    # Check that the settings for different types are distinct
    settings_by_type = {s.notification_type: s for s in all_settings}
    assert NotificationType.SYSTEM in settings_by_type
    assert NotificationType.TASK in settings_by_type
    assert settings_by_type[NotificationType.TASK].push_enabled == True
    assert settings_by_type[NotificationType.SYSTEM].push_enabled == False
    
    # Clean up
    await test_session.delete(system_settings)
    await test_session.delete(task_settings)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notification_template(test_session):
    """Test creating and using notification templates"""
    # Create a notification template
    template = NotificationTemplate(
        name="task_assignment",
        notification_type=NotificationType.TASK,
        title_template="New Task: {task_title}",
        content_template="You have been assigned a new task: {task_title}. Due date: {due_date}",
        email_subject_template="[Task] {task_title} Assigned to You",
        email_body_template="<p>Hello {user_name},</p><p>You have been assigned a new task:</p><p><strong>{task_title}</strong></p><p>Due date: {due_date}</p>",
        sms_template="New task assigned: {task_title}. Due: {due_date}",
        default_icon="task-icon",
        is_active=True
    )
    
    test_session.add(template)
    await test_session.commit()
    
    # Query the template
    stmt = select(NotificationTemplate).where(NotificationTemplate.name == "task_assignment")
    result = await test_session.execute(stmt)
    fetched_template = result.scalars().first()
    
    # Assert template was created correctly
    assert fetched_template is not None
    assert fetched_template.notification_type == NotificationType.TASK
    assert fetched_template.title_template == "New Task: {task_title}"
    assert "You have been assigned a new task" in fetched_template.content_template
    assert fetched_template.is_active == True
    
    # Simulate using the template (string format operation)
    template_data = {
        "task_title": "Complete Project Report",
        "due_date": "2025-05-15",
        "user_name": "John"
    }
    
    title = fetched_template.title_template.format(**template_data)
    content = fetched_template.content_template.format(**template_data)
    
    assert title == "New Task: Complete Project Report"
    assert "Complete Project Report" in content
    assert "2025-05-15" in content
    
    # Update template
    fetched_template.is_active = False
    await test_session.commit()
    
    # Query again
    result = await test_session.execute(stmt)
    updated_template = result.scalars().first()
    
    # Assert template was updated
    assert updated_template.is_active == False
    
    # Clean up
    await test_session.delete(template)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notifications_for_multiple_users(test_session):
    """Test creating notifications for multiple users"""
    # Create users
    user1 = User(
        email="user1@example.com",
        username="user1",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    user2 = User(
        email="user2@example.com",
        username="user2",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([user1, user2])
    await test_session.flush()
    
    # Create notifications for both users
    notification1 = Notification(
        user_id=user1.id,
        title="Message for User 1",
        content="This is a notification for user 1",
        notification_type=NotificationType.MESSAGE,
        priority=NotificationPriority.NORMAL
    )
    
    notification2 = Notification(
        user_id=user2.id,
        title="Task for User 2",
        content="This is a notification for user 2",
        notification_type=NotificationType.TASK,
        priority=NotificationPriority.HIGH
    )
    
    notification3 = Notification(
        user_id=user1.id,
        title="Meeting for User 1",
        content="This is another notification for user 1",
        notification_type=NotificationType.MEETING,
        priority=NotificationPriority.NORMAL
    )
    
    test_session.add_all([notification1, notification2, notification3])
    await test_session.commit()
    
    # Query notifications for user1
    stmt = select(Notification).where(Notification.user_id == user1.id)
    result = await test_session.execute(stmt)
    user1_notifications = result.scalars().all()
    
    # User1 should have 2 notifications
    assert len(user1_notifications) == 2
    notification_titles = [n.title for n in user1_notifications]
    assert "Message for User 1" in notification_titles
    assert "Meeting for User 1" in notification_titles
    
    # Query notifications for user2
    stmt = select(Notification).where(Notification.user_id == user2.id)
    result = await test_session.execute(stmt)
    user2_notifications = result.scalars().all()
    
    # User2 should have 1 notification
    assert len(user2_notifications) == 1
    assert user2_notifications[0].title == "Task for User 2"
    
    # Clean up
    for notification in [notification1, notification2, notification3]:
        await test_session.delete(notification)
    
    await test_session.delete(user1)
    await test_session.delete(user2)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notification_with_action_url(test_session):
    """Test notifications with action URLs"""
    # Create a user
    user = User(
        email="action_test@example.com",
        username="action_test_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a notification with an action URL
    notification = Notification(
        user_id=user.id,
        title="Document Shared",
        content="A new document has been shared with you",
        notification_type=NotificationType.DOCUMENT,
        priority=NotificationPriority.NORMAL,
        resource_type="document",
        resource_id=123,
        action_url="/documents/123"
    )
    
    test_session.add(notification)
    await test_session.commit()
    
    # Query the notification
    stmt = select(Notification).where(Notification.id == notification.id)
    result = await test_session.execute(stmt)
    fetched_notification = result.scalars().first()
    
    # Assert action URL was saved correctly
    assert fetched_notification is not None
    assert fetched_notification.action_url == "/documents/123"
    assert fetched_notification.resource_type == "document"
    assert fetched_notification.resource_id == 123
    
    # Clean up
    await test_session.delete(notification)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notification_with_complex_json_data(test_session):
    """Test notifications with complex JSON data"""
    # Create a user
    user = User(
        email="json_test@example.com",
        username="json_test_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create a notification with complex JSON data
    complex_data = {
        "project": {
            "id": 42,
            "name": "Annual Report",
            "progress": 75.5
        },
        "assignees": [
            {"id": 101, "name": "Alice"},
            {"id": 102, "name": "Bob"}
        ],
        "tags": ["urgent", "report", "finance"],
        "metrics": {
            "estimated_hours": 40,
            "completed_hours": 30
        }
    }
    
    notification = Notification(
        user_id=user.id,
        title="Project Update",
        content="The project 'Annual Report' has been updated",
        notification_type=NotificationType.PROJECT,
        priority=NotificationPriority.HIGH,
        resource_type="project",
        resource_id=42,
        data=complex_data
    )
    
    test_session.add(notification)
    await test_session.commit()
    
    # Query the notification
    stmt = select(Notification).where(Notification.id == notification.id)
    result = await test_session.execute(stmt)
    fetched_notification = result.scalars().first()
    
    # Assert JSON data was stored and retrieved correctly
    assert fetched_notification is not None
    assert fetched_notification.data["project"]["name"] == "Annual Report"
    assert fetched_notification.data["project"]["progress"] == 75.5
    assert len(fetched_notification.data["assignees"]) == 2
    assert fetched_notification.data["assignees"][0]["name"] == "Alice"
    assert fetched_notification.data["tags"] == ["urgent", "report", "finance"]
    assert fetched_notification.data["metrics"]["completed_hours"] == 30
    
    # Clean up
    await test_session.delete(notification)
    await test_session.delete(user)
    await test_session.commit()


@pytest.mark.asyncio
async def test_notification_cascade_delete(test_session):
    """Test that notifications are deleted when a user is deleted (cascade)"""
    # Create a user
    user = User(
        email="cascade_test@example.com",
        username="cascade_test_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create multiple notifications for the user
    notification1 = Notification(
        user_id=user.id,
        title="Notification 1",
        content="First test notification",
        notification_type=NotificationType.SYSTEM,
        priority=NotificationPriority.NORMAL
    )
    
    notification2 = Notification(
        user_id=user.id,
        title="Notification 2",
        content="Second test notification",
        notification_type=NotificationType.MESSAGE,
        priority=NotificationPriority.LOW
    )
    
    test_session.add_all([notification1, notification2])
    await test_session.commit()
    
    # Get the notification IDs before deleting the user
    notification_ids = [notification1.id, notification2.id]
    
    # Delete the user
    await test_session.delete(user)
    await test_session.commit()
    
    # Try to query the notifications after user deletion
    stmt = select(Notification).where(Notification.id.in_(notification_ids))
    result = await test_session.execute(stmt)
    remaining_notifications = result.scalars().all()
    
    # Assert that notifications were cascaded deleted
    assert len(remaining_notifications) == 0

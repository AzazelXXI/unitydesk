import pytest
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import uuid
from src.models.messenger import Chat, ChatMember, Message, ChatType, MessageType
from src.models.user import User

# Khai báo biến MODELS_IMPORTED để các test có thể kiểm tra
MODELS_IMPORTED = True

@pytest.mark.asyncio
async def test_session_fixture(test_session):
    assert test_session is not None

@pytest.mark.asyncio
async def test_create_direct_chat(test_session):
    """Test creating a direct (1-1) chat"""
    if not MODELS_IMPORTED:
        pytest.skip("Required messenger models not available")
    
    # Create two users
    user1 = User(
        email="user1@example.com",
        username="user1",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    user2 = User(
        email="user2@example.com",
        username="user2",
        hashed_password="hashedpassword456",
        is_active=True
    )
    
    test_session.add_all([user1, user2])
    await test_session.flush()
    
    # Create a direct chat
    chat = Chat(
        chat_type=ChatType.DIRECT,
        owner_id=user1.id,
        is_active=True
    )
    
    test_session.add(chat)
    await test_session.flush()
    
    # Add members
    member1 = ChatMember(
        chat_id=chat.id,
        user_id=user1.id,
        is_admin=True  # Owner is admin
    )
    
    member2 = ChatMember(
        chat_id=chat.id,
        user_id=user2.id,
        is_admin=False
    )
    
    test_session.add_all([member1, member2])
    await test_session.commit()
    
    # Query the chat with members
    stmt = select(Chat).options(
        joinedload(Chat.members).joinedload(ChatMember.user)
    ).where(Chat.id == chat.id)
    
    result = await test_session.execute(stmt)
    fetched_chat = result.scalars().first()
    
    # Assert chat was created correctly
    assert fetched_chat is not None
    assert fetched_chat.chat_type == ChatType.DIRECT
    assert len(fetched_chat.members) == 2
    
    # Clean up
    await test_session.delete(member1)
    await test_session.delete(member2)
    await test_session.delete(chat)
    await test_session.delete(user1)
    await test_session.delete(user2)
    await test_session.commit()

@pytest.mark.asyncio
async def test_create_group_chat(test_session):
    """Test creating a group chat"""
    if not MODELS_IMPORTED:
        pytest.skip("Required messenger models not available")
    
    # Create users
    owner = User(
        email="owner@example.com",
        username="owner_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    member1 = User(
        email="member1@example.com",
        username="member_user1",
        hashed_password="hashedpassword456",
        is_active=True
    )
    
    member2 = User(
        email="member2@example.com",
        username="member_user2",
        hashed_password="hashedpassword789",
        is_active=True
    )
    
    test_session.add_all([owner, member1, member2])
    await test_session.flush()
    
    # Create group chat
    chat = Chat(
        name="Test Group Chat",
        description="A test group chat for testing",
        chat_type=ChatType.GROUP,
        owner_id=owner.id,
        avatar_url="https://example.com/avatar.jpg"
    )
    
    test_session.add(chat)
    await test_session.flush()
    
    # Add members
    chat_members = [
        ChatMember(chat_id=chat.id, user_id=owner.id, is_admin=True),
        ChatMember(chat_id=chat.id, user_id=member1.id, is_admin=False),
        ChatMember(chat_id=chat.id, user_id=member2.id, is_admin=False)
    ]
    
    test_session.add_all(chat_members)
    await test_session.commit()
    
    # Query the chat
    stmt = select(Chat).options(
        joinedload(Chat.members)
    ).where(Chat.id == chat.id)
    
    result = await test_session.execute(stmt)
    fetched_chat = result.scalars().first()
    
    # Assert group chat attributes
    assert fetched_chat is not None
    assert fetched_chat.chat_type == ChatType.GROUP
    assert fetched_chat.name == "Test Group Chat"
    assert fetched_chat.description == "A test group chat for testing"
    assert len(fetched_chat.members) == 3
    
    # Verify admin
    admin_members = [m for m in fetched_chat.members if m.is_admin]
    assert len(admin_members) == 1
    assert admin_members[0].user_id == owner.id
    
    # Clean up
    for cm in chat_members:
        await test_session.delete(cm)
    await test_session.delete(chat)
    await test_session.delete(owner)
    await test_session.delete(member1)
    await test_session.delete(member2)
    await test_session.commit()

@pytest.mark.asyncio
async def test_send_messages(test_session):
    """Test sending messages in a chat"""
    if not MODELS_IMPORTED:
        pytest.skip("Required messenger models not available")
    
    # Create users
    user1 = User(
        email="sender@example.com",
        username="sender_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    user2 = User(
        email="receiver@example.com",
        username="receiver_user",
        hashed_password="hashedpassword456",
        is_active=True
    )
    
    test_session.add_all([user1, user2])
    await test_session.flush()
    
    # Create chat
    chat = Chat(
        chat_type=ChatType.DIRECT,
        owner_id=user1.id
    )
    
    test_session.add(chat)
    await test_session.flush()
    
    # Add members
    chat_members = [
        ChatMember(chat_id=chat.id, user_id=user1.id, is_admin=True),
        ChatMember(chat_id=chat.id, user_id=user2.id, is_admin=False)
    ]
    
    test_session.add_all(chat_members)
    await test_session.flush()
    
    # Send messages
    message1 = Message(
        chat_id=chat.id,
        sender_id=user1.id,
        content="Hello, this is a test message",
        message_type=MessageType.TEXT
    )
    
    test_session.add(message1)
    await test_session.flush()
    
    # Reply to first message
    message2 = Message(
        chat_id=chat.id,
        sender_id=user2.id,
        content="Hi there! I received your message",
        message_type=MessageType.TEXT,
        parent_id=message1.id  # This is a reply
    )
    
    test_session.add(message2)
    await test_session.commit()
    
    # Query the messages
    stmt = select(Message).options(
        joinedload(Message.sender),
        joinedload(Message.replies),
        joinedload(Message.parent_message)
    ).where(Message.chat_id == chat.id).order_by(Message.created_at)
    
    result = await test_session.execute(stmt)
    messages = result.scalars().unique().all()
    
    # Assert messages were sent correctly
    assert len(messages) == 2
    assert messages[0].content == "Hello, this is a test message"
    assert messages[0].sender_id == user1.id
    assert len(messages[0].replies) == 1
    
    assert messages[1].content == "Hi there! I received your message"
    assert messages[1].sender_id == user2.id
    assert messages[1].parent_id == message1.id
    assert messages[1].parent_message.id == message1.id
    
    # Clean up
    await test_session.delete(message2)
    await test_session.delete(message1)
    for cm in chat_members:
        await test_session.delete(cm)
    await test_session.delete(chat)
    await test_session.delete(user1)
    await test_session.delete(user2)
    await test_session.commit()

@pytest.mark.asyncio
async def test_message_with_attachment(test_session):
    """Test sending a message with attachment"""
    if not MODELS_IMPORTED:
        pytest.skip("Required messenger models not available")
    
    # Create user
    user = User(
        email="attachment@example.com",
        username="attachment_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create chat
    chat = Chat(
        chat_type=ChatType.DIRECT,
        owner_id=user.id
    )
    
    test_session.add(chat)
    await test_session.flush()
    
    # Add member
    chat_member = ChatMember(
        chat_id=chat.id,
        user_id=user.id,
        is_admin=True
    )
    
    test_session.add(chat_member)
    await test_session.flush()
    
    # Create message with attachment
    image_message = Message(
        chat_id=chat.id,
        sender_id=user.id,
        content="Check out this image",
        message_type=MessageType.IMAGE,
        attachment_url="https://example.com/image.jpg"
    )
    
    file_message = Message(
        chat_id=chat.id,
        sender_id=user.id,
        content="Here's the document you requested",
        message_type=MessageType.FILE,
        attachment_url="https://example.com/document.pdf"
    )
    
    test_session.add_all([image_message, file_message])
    await test_session.commit()
    
    # Query the messages
    stmt = select(Message).where(
        Message.chat_id == chat.id,
        Message.message_type != MessageType.TEXT
    )
    
    result = await test_session.execute(stmt)
    attachment_messages = result.scalars().all()
    
    # Assert attachment was saved correctly
    assert len(attachment_messages) == 2
    
    image_msg = next((m for m in attachment_messages if m.message_type == MessageType.IMAGE), None)
    assert image_msg is not None
    assert image_msg.attachment_url == "https://example.com/image.jpg"
    
    file_msg = next((m for m in attachment_messages if m.message_type == MessageType.FILE), None)
    assert file_msg is not None
    assert file_msg.attachment_url == "https://example.com/document.pdf"
    
    # Clean up
    await test_session.delete(image_message)
    await test_session.delete(file_message)
    await test_session.delete(chat_member)
    await test_session.delete(chat)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_edit_message(test_session):
    """Test editing a message"""
    if not MODELS_IMPORTED:
        pytest.skip("Required messenger models not available")
    
    # Create user
    user = User(
        email="editor@example.com",
        username="editor_user",
        hashed_password="hashedpassword123",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.flush()
    
    # Create chat
    chat = Chat(
        chat_type=ChatType.DIRECT,
        owner_id=user.id
    )
    
    test_session.add(chat)
    await test_session.flush()
    
    # Add member
    chat_member = ChatMember(
        chat_id=chat.id,
        user_id=user.id,
        is_admin=True
    )
    
    test_session.add(chat_member)
    await test_session.flush()
    
    # Create message
    message = Message(
        chat_id=chat.id,
        sender_id=user.id,
        content="Original message content",
        message_type=MessageType.TEXT
    )
    
    test_session.add(message)
    await test_session.commit()
    
    # Edit message
    edited_time = datetime.utcnow()
    message.content = "Edited message content"
    message.is_edited = True
    message.edited_at = edited_time
    
    await test_session.commit()
    
    # Query the message
    stmt = select(Message).where(Message.id == message.id)
    result = await test_session.execute(stmt)
    edited_message = result.scalars().first()
    
    # Assert message was edited
    assert edited_message.content == "Edited message content"
    assert edited_message.is_edited is True
    assert edited_message.edited_at is not None
    
    # Clean up
    await test_session.delete(message)
    await test_session.delete(chat_member)
    await test_session.delete(chat)
    await test_session.delete(user)
    await test_session.commit()

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.controllers import user_controller
from src.schemas.user import UserCreate, UserProfileCreate, UserRole


@pytest.mark.asyncio
async def test_create_and_get_user():
    # Prepare user data with more specific mock-like values
    user_data = UserCreate(
        email="specific.mock.user@example.com",
        username="specificmockuser01",
        password="MockPassword123!",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        profile=UserProfileCreate(
            first_name="SpecificMockFirstName",
            last_name="SpecificMockLastName",
            display_name="Specific Mock User 01",
            avatar_url="https://example.com/avatar/specificmockuser01.png",
            phone_number="987-654-3210",
            department="MockTech Department",  # Populated from mock data
            position="Mock Developer",  # Populated from mock data (schema allows, model might not store)
            bio="This is a specific mock user profile for integration testing.",
            timezone="America/New_York",
        ),
    )

    # Get a real DB session
    async for db in get_db():
        # Create user
        user = await user_controller.create_user(db, user_data)
        assert user.id is not None
        assert user.email == user_data.email
        assert user.username == user_data.username
        # Fetch user by username
        fetched = await user_controller.get_user_by_username(db, user_data.username)
        assert fetched is not None
        assert fetched.email == user_data.email
        # Do not delete or rollback: keep data as proof
        break

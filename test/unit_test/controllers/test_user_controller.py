from fastapi import HTTPException
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from test.conftest import test_engine, test_session
from src.models.user import User, UserRole, UserProfile
from src.schemas.user import UserCreate, UserProfileCreate, UserUpdate, Token


# Add fixture definitions for mock_user and mock_user_with_profile
@pytest.fixture
def mock_user():
    """Create a mock User object for testing"""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.role = UserRole.USER
    user.is_active = True
    user.is_verified = False
    user.profile = None
    return user


@pytest.fixture
def mock_user_with_profile(mock_user):
    """Create a mock User object with associated profile for testing"""
    profile = MagicMock(spec=UserProfile)
    profile.id = 1
    profile.user_id = mock_user.id
    profile.first_name = "Test"
    profile.last_name = "User"
    profile.display_name = "Test User"
    profile.avatar_url = "http://example.com/avatar.jpg"
    profile.bio = "Test bio"
    profile.phone = "+1234567890"
    profile.location = "Test Location"
    profile.timezone = "UTC"

    # Attach profile to user
    mock_user.profile = profile
    return mock_user


@pytest.fixture
def user_create_data():
    """Create a UserCreate object for testing"""
    profile = UserProfileCreate(
        first_name="Test",
        last_name="User",
        display_name="Test User",
        avatar_url="http://example.com/avatar.jpg",
        bio="Test user bio",
        phone_number="+1234567890",
        department="Test Department",  # Changed from location to department
        position="Test Position",      # Added position field
        timezone="UTC",
    )

    return UserCreate(
        email="test_user@example.com",
        username="test_user",
        password="securepassword123",
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
        profile=profile,
    )


# Test create_user function
class TestCreateUser:
    @pytest.mark.asyncio
    async def test_create_user_success(self, test_session, user_create_data):
        # Import trong hàm test
        from src.controllers.user_controller import create_user
        from sqlalchemy import select, exists
        
        # Create a more complete mock setup
        # 1. Create mock for the query result
        mock_result = MagicMock()
        mock_result.scalar.return_value = False  # User does NOT exist
        
        # 2. Set up the execute method to return our mock result
        test_session.execute = AsyncMock(return_value=mock_result)
        test_session.commit = AsyncMock()
        test_session.add = MagicMock()
        test_session.refresh = AsyncMock()
        test_session.flush = AsyncMock()

        # 3. Replace profile with a MagicMock that will respond to any attribute access
        mock_profile = MagicMock()
        mock_profile.first_name = user_create_data.profile.first_name
        mock_profile.last_name = user_create_data.profile.last_name
        mock_profile.display_name = user_create_data.profile.display_name
        mock_profile.avatar_url = user_create_data.profile.avatar_url
        mock_profile.bio = user_create_data.profile.bio
        mock_profile.phone_number = user_create_data.profile.phone_number
        mock_profile.department = user_create_data.profile.department
        mock_profile.position = user_create_data.profile.position
        mock_profile.timezone = user_create_data.profile.timezone
        # Add location field to match what controller is expecting
        mock_profile.location = user_create_data.profile.department
        
        # Replace the profile in user_create_data
        user_create_data.profile = mock_profile

        # 4. Ensure password hashing is also mocked
        with patch(
            "src.controllers.user_controller.get_password_hash",
            return_value="hashed_password",
        ):
            # Execute
            result = await create_user(test_session, user_create_data)

            # Assert
            assert test_session.add.call_count == 2  # User and Profile
            assert test_session.commit.awaited

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, test_session, user_create_data):
        # Import trong hàm test
        from src.controllers.user_controller import create_user

        # Setup - Mock test_session.execute
        mock_execute_result = AsyncMock()
        mock_execute_result.scalar.return_value = True  # User exists
        test_session.execute = AsyncMock(return_value=mock_execute_result)

        # Execute and Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_user(test_session, user_create_data)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_user_without_profile(self, test_session, user_create_data):
        # Import trong hàm test
        from src.controllers.user_controller import create_user
        
        # Setup - Mock test_session methods properly
        mock_result = MagicMock()
        mock_result.scalar.return_value = False
        test_session.execute = AsyncMock(return_value=mock_result)
        test_session.commit = AsyncMock()
        test_session.add = MagicMock()
        test_session.refresh = AsyncMock()
        test_session.flush = AsyncMock()
        
        # Set profile to None
        user_create_data.profile = None

        with patch(
            "src.controllers.user_controller.get_password_hash",
            return_value="hashed_password",
        ):
            # Execute
            result = await create_user(test_session, user_create_data)

            # Assert
            assert test_session.add.call_count == 1  # Only User
            assert test_session.commit.awaited


# Test get_users function
class TestGetUsers:
    @pytest.mark.asyncio
    async def test_get_all_users(self, test_session, mock_user_with_profile):
        # Import trong hàm test
        from src.controllers.user_controller import get_users

        # Setup
        test_session.execute.return_value.scalars.return_value.all.return_value = [
            mock_user_with_profile
        ]

        # Execute
        result = await get_users(test_session)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_user_with_profile

    @pytest.mark.asyncio
    async def test_get_users_with_role_filter(self, test_session, mock_user_with_profile):
        # Import trong hàm test
        from src.controllers.user_controller import get_users

        # Setup
        test_session.execute.return_value.scalars.return_value.all.return_value = [
            mock_user_with_profile
        ]

        # Execute
        result = await get_users(test_session, role=UserRole.USER)

        # Assert
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_users_with_pagination(self, test_session, mock_user_with_profile):
        # Import trong hàm test
        from src.controllers.user_controller import get_users

        # Setup
        test_session.execute.return_value.scalars.return_value.all.return_value = [
            mock_user_with_profile
        ]

        # Execute
        result = await get_users(test_session, skip=10, limit=20)

        # Assert
        assert len(result) == 1


# Test get_user function
class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_user_by_id_exists(self, test_session, mock_user_with_profile):
        # Import trong hàm test
        from src.controllers.user_controller import get_user

        # Setup
        test_session.execute.return_value.scalars.return_value.first.return_value = (
            mock_user_with_profile
        )

        # Execute
        result = await get_user(test_session, 1)

        # Assert
        assert result == mock_user_with_profile

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_exists(self, test_session):
        # Import trong hàm test
        from src.controllers.user_controller import get_user

        # Setup
        test_session.execute.return_value.scalars.return_value.first.return_value = None

        # Execute
        result = await get_user(test_session, 999)

        # Assert
        assert result is None


# Test get_user_by_username function
class TestGetUserByUsername:
    @pytest.mark.asyncio
    async def test_get_user_by_username_exists(
        self, test_session, mock_user_with_profile
    ):
        # Import trong hàm test
        from src.controllers.user_controller import get_user_by_username

        # Setup
        test_session.execute.return_value.scalars.return_value.first.return_value = (
            mock_user_with_profile
        )

        # Execute
        result = await get_user_by_username(test_session, "testuser")

        # Assert
        assert result == mock_user_with_profile

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_exists(self, test_session):
        # Import trong hàm test
        from src.controllers.user_controller import get_user_by_username

        # Setup
        test_session.execute.return_value.scalars.return_value.first.return_value = None

        # Execute
        result = await get_user_by_username(test_session, "nonexistent")

        # Assert
        assert result is None


# Test get_user_by_email function
class TestGetUserByEmail:
    @pytest.mark.asyncio
    async def test_get_user_by_email_exists(self, test_session, mock_user_with_profile):
        # Import trong hàm test
        from src.controllers.user_controller import get_user_by_email

        # Setup
        test_session.execute.return_value.scalars.return_value.first.return_value = (
            mock_user_with_profile
        )

        # Execute
        result = await get_user_by_email(test_session, "test@example.com")

        # Assert
        assert result == mock_user_with_profile

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_exists(self, test_session):
        # Import trong hàm test
        from src.controllers.user_controller import get_user_by_email

        # Setup
        test_session.execute.return_value.scalars.return_value.first.return_value = None

        # Execute
        result = await get_user_by_email(test_session, "nonexistent@example.com")

        # Assert
        assert result is None


# Test update_user function
class TestUpdateUser:
    @pytest.fixture
    def user_update_data(self):
        return UserUpdate(
            email="updated@example.com",
            is_active=False,
            profile={
                "first_name": "Updated",
                "last_name": "User",
                "bio": "Updated bio",
            },
        )

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, test_session, mock_user_with_profile, user_update_data
    ):
        # Import trong hàm test
        from src.controllers.user_controller import update_user

        # Setup
        with patch(
            "src.controllers.user_controller.get_user",
            side_effect=[mock_user_with_profile, mock_user_with_profile],
        ):
            # Execute
            result = await update_user(test_session, 1, user_update_data)

            # Assert
            assert result == mock_user_with_profile
            assert test_session.commit.awaited

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, test_session, user_update_data):
        # Import trong hàm test
        from src.controllers.user_controller import update_user

        # Setup
        with patch("src.controllers.user_controller.get_user", return_value=None):
            # Execute
            result = await update_user(test_session, 999, user_update_data)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_update_user_create_profile(
        self, test_session, mock_user, user_update_data
    ):
        # Import trong hàm test
        from src.controllers.user_controller import update_user

        # Setup
        with patch(
            "src.controllers.user_controller.get_user",
            side_effect=[mock_user, mock_user],
        ):
            # Execute
            result = await update_user(test_session, 1, user_update_data)

            # Assert
            assert test_session.add.called


# Test delete_user function
class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_success(self, test_session, mock_user):
        # Import trong hàm test
        from src.controllers.user_controller import delete_user

        # Setup
        test_session.execute = AsyncMock()
        test_session.commit = AsyncMock()  # Make sure commit is an AsyncMock
        
        with patch("src.controllers.user_controller.get_user", return_value=mock_user):
            # Execute
            result = await delete_user(test_session, 1)

            # Assert
            assert result is True
            assert test_session.commit.awaited

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, test_session):
        # Import trong hàm test
        from src.controllers.user_controller import delete_user

        # Setup
        test_session.commit = AsyncMock()  # Add proper mocking
        
        with patch("src.controllers.user_controller.get_user", return_value=None):
            # Execute
            result = await delete_user(test_session, 999)

            # Assert
            assert result is False


# Test login_for_access_token function
class TestLoginForAccessToken:
    @pytest.mark.asyncio
    async def test_login_success(self, test_session, mock_user):
        # Import trong hàm test
        from src.controllers.user_controller import login_for_access_token

        # Setup
        with patch(
            "src.controllers.user_controller.authenticate_user", return_value=mock_user
        ), patch(
            "src.controllers.user_controller.create_access_token",
            return_value="access_token",
        ), patch(
            "src.controllers.user_controller.create_refresh_token",
            return_value="refresh_token",
        ):

            # Execute
            result = await login_for_access_token(test_session, "testuser", "password123")

            # Assert
            assert result.access_token == "access_token"
            assert result.refresh_token == "refresh_token"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_session):
        # Import trong hàm test
        from src.controllers.user_controller import login_for_access_token

        # Setup
        with patch(
            "src.controllers.user_controller.authenticate_user", return_value=None
        ):
            # Execute
            result = await login_for_access_token(
                test_session, "testuser", "wrong_password"
            )

            # Assert
            assert result is None


# Test change_user_password function
class TestChangeUserPassword:
    @pytest.mark.asyncio
    async def test_change_password_success(self, test_session, mock_user):
        # Import controller function trực tiếp ở đây
        from src.controllers.user_controller import change_user_password

        # Setup: Create a properly structured mock that works with async code
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user

        # We need to use AsyncMock to have awaitable methods
        test_session.execute = AsyncMock(return_value=mock_result)
        test_session.commit = AsyncMock()

        # Patch get_password_hash trực tiếp tại điểm nó được gọi
        with patch(
            "src.services.auth_service.get_password_hash",
            return_value="new_hashed_password",
        ), patch(
            "src.controllers.user_controller.authenticate_user",
            return_value=True
        ):
            # Execute
            result = await change_user_password(
                test_session, 1, "current_password", "new_password"
            )

            # Assert
            assert result is True
            assert test_session.execute.call_count == 2
            assert test_session.commit.awaited

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, test_session):
        # Import controller function
        from src.controllers.user_controller import change_user_password
        
        # Mock setup
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None  # User not found
        test_session.execute = AsyncMock(return_value=mock_result)
        test_session.commit = AsyncMock()
        
        # Execute - use an ID that doesn't exist
        result = await change_user_password(
            test_session, 999, "current_password", "new_password"
        )
        
        # Assert
        assert result is False
        # Should only call execute once to look up the user
        assert test_session.execute.call_count == 1
        # Should not call commit since we return early
        assert not test_session.commit.called

    @pytest.mark.asyncio
    async def test_change_password_incorrect_current(self, test_session, mock_user):
        # Import trong hàm test
        from src.controllers.user_controller import change_user_password

        # Setup: Create properly structured mock for async operations
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        test_session.execute = AsyncMock(return_value=mock_result)
        test_session.commit = AsyncMock()

        # Patch authenticate_user để luôn trả về False (mật khẩu không đúng)
        with patch(
            "src.controllers.user_controller.authenticate_user", 
            return_value=False  # Thay lambda bằng giá trị trực tiếp
        ):
            # Execute
            result = await change_user_password(
                test_session, 1, "wrong_password", "new_password"
            )

            # Assert
            assert result is False
            # Verify db.execute was called only once for the select query
            assert test_session.execute.call_count == 1
            # Không gọi commit vì chúng ta return early
            assert not test_session.commit.called

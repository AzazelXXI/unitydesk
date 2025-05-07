import pytest
from src.schemas import *


def test_user_base_schema_normalization():
    # test data
    user_role = UserRole.ADMIN
    is_active = True
    is_verified = False

    # create user_base
    user_base: UserBase = UserBase(
        username="testuser",
        email="testuser@example.com",
        role=user_role,
        is_active=is_active,
        is_verified=is_verified,
    )
    assert user_base.username == "testuser"
    assert user_base.email == "testuser@example.com"


def test_user_create_schema_normalization():
    # test data
    user_role = UserRole.ADMIN
    is_active = True
    is_verified = False  # create user_create
    user_create: UserCreate = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="testpassword123",
    )
    assert user_create.username == "testuser"
    assert user_create.email == "testuser@example.com"
    assert user_create.password == "testpassword123"


def test_user_base_schema_fields():
    user_base = UserBase(
        username="alice",
        email="alice@example.com",
        role=UserRole.USER,
        is_active=False,
        is_verified=True,
    )
    assert user_base.role == UserRole.USER
    assert user_base.is_active is False
    assert user_base.is_verified is True


def test_user_create_schema_missing_fields():
    from pydantic_core import ValidationError

    with pytest.raises(ValidationError):
        UserCreate(username="bob", email="bob@example.com")  # missing password


def test_user_create_schema_invalid_email():
    with pytest.raises(ValueError):
        UserCreate(username="bob", email="not-an-email", password="pass123")


def test_user_update_schema_partial_update():
    user_update = UserUpdate(email="newemail@example.com")
    assert user_update.email == "newemail@example.com"
    assert user_update.username is None


def test_user_role_enum():
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.USER.value == "user"
    assert UserRole.GUEST.value == "guest"


def test_user_base_schema_repr():
    user_base = UserBase(
        username="charlie",
        email="charlie@example.com",
        role=UserRole.GUEST,
        is_active=True,
        is_verified=False,
    )
    assert "charlie" in repr(user_base)
    assert "charlie@example.com" in repr(user_base)

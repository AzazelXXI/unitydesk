import sys
import os
from typing import Generator, AsyncGenerator
import urllib.parse
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_scoped_session,
)
from src.database import engine
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
from asyncio import current_task


@pytest.fixture()
def test_engine() -> Generator[AsyncEngine, None, None]:
    # Create connection URL with properly encoded password
    connection_url = "postgresql+asyncpg://postgres:azazeladmin@localhost:5432/testdb"
    engine = create_async_engine(
        connection_url,
        echo=True,
        # pool_size=20, max_overflow=0
    )
    yield engine


@pytest.fixture()
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    session_maker = sessionmaker(
        bind=test_engine, expire_on_commit=False, class_=AsyncSession
    )
    Session = async_scoped_session(session_maker, scopefunc=current_task)
    async with Session() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_db_after_test(test_engine):
    """
    Setup and teardown fixture for the database.
    This runs automatically for each test that uses the database.
    """
    from src.models.base import Base

    # Setup - Create tables before tests if they don't exist
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Teardown - Clean specific tables after tests instead of dropping all
    # This avoids circular dependency issues when dropping tables
    async with test_engine.begin() as conn:
        # To prevent circular dependency issues, we'll clean tables individually
        # rather than using drop_all
        await conn.execute(
            text("TRUNCATE users, user_profiles RESTART IDENTITY CASCADE")
        )
        # Add other tables as needed

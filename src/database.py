import os
from asyncio import current_task
from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_scoped_session,
)
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment variable with a fallback for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:#0Comatkhau@localhost:5432/csa_hello"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # pool_size=20, max_overflow=0
)

Base = declarative_base()

# Dependency for getting async DB session
async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    session_maker = sessionmaker(
        bind=engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    Session = async_scoped_session(session_maker, scopefunc=current_task)
    async with Session() as session:
        yield session

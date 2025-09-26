"""Pytest configuration"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


@pytest.fixture
async def async_session():
    """Create async session for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

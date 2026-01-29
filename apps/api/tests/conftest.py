"""
Shared test fixtures for Gaffer API tests.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool, NullPool

from app.config import Settings
from app.models import Base
from app.services.cache_service import CacheService, InMemoryCacheBackend


# =============================================================================
# Test Settings
# =============================================================================


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings with mocked credentials."""
    return Settings(
        app_env="test",
        frontend_url="http://localhost:3000",
        database_url="sqlite+aiosqlite:///:memory:",
        supabase_url="https://test.supabase.co",
        supabase_service_role_key="test-service-role-key",
        anthropic_api_key="test-anthropic-key",
        google_client_id="test-google-client-id",
        google_client_secret="test-google-client-secret",
        token_encryption_key=Fernet.generate_key().decode(),
        elevenlabs_api_key="test-elevenlabs-key",
        elevenlabs_voice_id="test-voice-id",
        redis_url=None,
    )


@pytest.fixture
def fernet_key() -> str:
    """Generate a valid Fernet key for token encryption tests."""
    return Fernet.generate_key().decode()


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for tests using SQLite in-memory."""
    import sqlite3
    from uuid import UUID as PyUUID

    # Register UUID adapter for SQLite
    sqlite3.register_adapter(PyUUID, lambda u: u.bytes)
    sqlite3.register_converter("UUID", lambda b: PyUUID(bytes=b))
    sqlite3.register_adapter(uuid4().__class__, lambda u: str(u))

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# =============================================================================
# PostgreSQL Fixtures (Integration Tests)
# =============================================================================


@pytest.fixture(scope="session")
def postgres_container():
    """
    Start a PostgreSQL container for integration tests.
    Requires Docker to be running.
    """
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="test_gaffer",
    )
    container.start()

    yield container

    container.stop()


@pytest.fixture(scope="session")
def postgres_url(postgres_container) -> str:
    """Get the PostgreSQL connection URL from the container."""
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    return f"postgresql+asyncpg://test:test@{host}:{port}/test_gaffer"


@pytest_asyncio.fixture(scope="function")
async def pg_engine(postgres_url):
    """Create async engine for integration tests using PostgreSQL."""
    engine = create_async_engine(
        postgres_url,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def pg_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a PostgreSQL test session for integration tests."""
    async_session_maker = async_sessionmaker(
        pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# =============================================================================
# Cache Fixtures
# =============================================================================


@pytest.fixture
def cache_service() -> CacheService:
    """Create an in-memory cache service for tests."""
    backend = InMemoryCacheBackend()
    return CacheService(backend)


@pytest.fixture
def mock_cache_service() -> MagicMock:
    """Create a mocked cache service."""
    mock = MagicMock(spec=CacheService)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.is_using_fallback = False
    return mock


# =============================================================================
# HTTP Client Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def async_client(
    db_session: AsyncSession,
    test_settings: Settings,
    cache_service: CacheService,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing endpoints."""
    from app.main import app
    from app.services.database import get_db
    from app.config import get_settings
    from app.services.cache_service import get_cache_service

    async def override_get_db():
        yield db_session

    def override_get_settings():
        return test_settings

    def override_get_cache_service():
        return cache_service

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_cache_service] = override_get_cache_service

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# =============================================================================
# User/Auth Fixtures
# =============================================================================


@pytest.fixture
def test_user_id() -> uuid4:
    """Generate a test user ID as UUID object."""
    return uuid4()


@pytest.fixture
def auth_headers(test_user_id: str) -> dict[str, str]:
    """Create mock authorization headers."""
    return {"Authorization": f"Bearer test-jwt-token-{test_user_id}"}


# =============================================================================
# External API Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_google_oauth_response():
    """Mock successful Google OAuth token refresh response."""
    return {
        "access_token": "new-access-token-12345",
        "expires_in": 3600,
        "token_type": "Bearer",
    }


@pytest.fixture
def mock_google_calendar_events():
    """Mock Google Calendar events response."""
    return {
        "items": [
            {
                "id": "event-123",
                "summary": "Team Standup",
                "description": "Daily sync meeting",
                "start": {"dateTime": "2024-01-15T09:00:00Z"},
                "end": {"dateTime": "2024-01-15T09:30:00Z"},
                "location": "Zoom",
                "attendees": [
                    {"email": "user1@example.com"},
                    {"email": "user2@example.com"},
                ],
                "etag": '"etag-123"',
            },
            {
                "id": "event-456",
                "summary": "Product Review",
                "start": {"dateTime": "2024-01-15T14:00:00Z"},
                "end": {"dateTime": "2024-01-15T15:00:00Z"},
                "etag": '"etag-456"',
            },
        ],
        "nextPageToken": None,
    }


@pytest.fixture
def mock_claude_response():
    """Mock Anthropic Claude API response."""

    class MockContent:
        text = "[excited] This is YOUR moment! [pause] You've prepared for this! [shouts] Now GO GET THEM!"

    class MockMessage:
        content = [MockContent()]

    return MockMessage()


@pytest.fixture
def mock_elevenlabs_audio():
    """Mock ElevenLabs audio generation response."""
    return iter([b"\xff\xfb\x90\x00" + b"\x00" * 100])


# =============================================================================
# Time Fixtures
# =============================================================================


@pytest.fixture
def now_utc() -> datetime:
    """Get current UTC time for test assertions."""
    return datetime.now(timezone.utc)

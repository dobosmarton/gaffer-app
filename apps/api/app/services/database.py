from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# Create async engine
# Note: statement_cache_size=0 is required for PgBouncer compatibility
# (Supabase uses PgBouncer in transaction mode which doesn't support prepared statements)
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",  # Log SQL in dev
    pool_pre_ping=True,  # Verify connections before using
    connect_args={
        "statement_cache_size": 0,  # Disable prepared statement caching for PgBouncer
    },
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

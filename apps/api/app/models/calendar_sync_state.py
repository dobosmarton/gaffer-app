from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class CalendarSyncState(Base):
    """Tracks calendar sync state for each user."""

    __tablename__ = "calendar_sync_state"

    # FK constraint exists in database, not defined here to avoid SQLAlchemy
    # trying to resolve auth.users which is a Supabase internal table
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    last_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CalendarSyncState(user_id={self.user_id}, last_sync={self.last_sync})>"

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class CalendarEvent(Base):
    """Cached calendar events from Google Calendar."""

    __tablename__ = "calendar_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    # FK constraint exists in database, not defined here to avoid SQLAlchemy
    # trying to resolve auth.users which is a Supabase internal table
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    google_event_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attendees_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        nullable=False,
    )

    # Importance scoring fields
    importance_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    importance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importance_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "google_event_id", name="unique_user_google_event"),
        Index("idx_calendar_events_user_id", "user_id"),
        Index("idx_calendar_events_user_start", "user_id", "start_time"),
        Index("idx_calendar_events_google_id", "google_event_id"),
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(id={self.id}, title={self.title})>"

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class HypeRecord(Base):
    """Stores generated hype text and audio for calendar events."""

    __tablename__ = "hype_records"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    calendar_event_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    google_event_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_title: Mapped[str] = mapped_column(Text, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    manager_style: Mapped[str] = mapped_column(Text, server_default="ferguson", nullable=False)
    hype_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, server_default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_hype_records_user_id", "user_id"),
        Index("idx_hype_records_calendar_event", "calendar_event_id"),
        Index("idx_hype_records_google_event", "google_event_id"),
        Index("idx_hype_records_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<HypeRecord(id={self.id}, event_title={self.event_title}, status={self.status})>"

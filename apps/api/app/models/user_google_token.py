from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserGoogleToken(Base):
    """Stores encrypted Google OAuth refresh tokens for users."""

    __tablename__ = "user_google_tokens"

    # FK constraint exists in database, not defined here to avoid SQLAlchemy
    # trying to resolve auth.users which is a Supabase internal table
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_user_google_tokens_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserGoogleToken(user_id={self.user_id})>"

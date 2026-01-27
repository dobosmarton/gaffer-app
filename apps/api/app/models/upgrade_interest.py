from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class UpgradeInterest(Base):
    """Tracks users who expressed interest in upgrading to a paid plan."""

    __tablename__ = "upgrade_interests"

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
        unique=True,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (Index("idx_upgrade_interests_user_id", "user_id"),)

    def __repr__(self) -> str:
        return f"<UpgradeInterest(user_id={self.user_id}, email={self.email})>"

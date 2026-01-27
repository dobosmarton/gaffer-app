from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class UserSubscription(Base):
    """Stores user subscription/plan information for usage limits."""

    __tablename__ = "user_subscriptions"

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
    plan_type: Mapped[str] = mapped_column(
        Text, server_default="free", nullable=False
    )
    monthly_limit: Mapped[int] = mapped_column(
        Integer, server_default="5", nullable=False
    )

    # Stripe fields (for future integration)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        Index("idx_user_subscriptions_user_id", "user_id"),
        Index("idx_user_subscriptions_stripe_customer", "stripe_customer_id"),
    )

    def __repr__(self) -> str:
        return f"<UserSubscription(user_id={self.user_id}, plan={self.plan_type}, limit={self.monthly_limit})>"

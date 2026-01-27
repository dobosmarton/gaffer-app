"""
Usage Service

Handles usage limits and subscription management for speech generation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HypeRecord as HypeRecordModel
from app.models import UserSubscription as UserSubscriptionModel

logger = logging.getLogger(__name__)


@dataclass
class UsageInfo:
    """Current usage information for a user."""

    used: int
    limit: int
    plan: str
    resets_at: datetime
    can_generate: bool


class UsageService:
    """Service for managing usage limits."""

    async def get_or_create_subscription(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> UserSubscriptionModel:
        """
        Get existing subscription or create a free one.

        Args:
            db: Database session
            user_id: The user's ID

        Returns:
            The user's subscription record
        """
        # Try to get existing subscription
        stmt = select(UserSubscriptionModel).where(
            UserSubscriptionModel.user_id == user_id
        )
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            return subscription

        # Create new free subscription
        now = datetime.now(timezone.utc)
        subscription = UserSubscriptionModel(
            user_id=user_id,
            plan_type="free",
            monthly_limit=5,
            created_at=now,
            updated_at=now,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Created free subscription for user {user_id[:8]}...")
        return subscription

    async def get_monthly_usage(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> int:
        """
        Count speech generations this month.

        Only counts successful generations (status != 'error').

        Args:
            db: Database session
            user_id: The user's ID

        Returns:
            Number of generations this month
        """
        # Get first day of current month
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.count(HypeRecordModel.id)).where(
            and_(
                HypeRecordModel.user_id == user_id,
                HypeRecordModel.created_at >= first_of_month,
                HypeRecordModel.status != "error",
            )
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0

        return count

    async def get_usage_info(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> UsageInfo:
        """
        Get complete usage information for a user.

        Args:
            db: Database session
            user_id: The user's ID

        Returns:
            UsageInfo with current usage and limits
        """
        subscription = await self.get_or_create_subscription(db, user_id)
        used = await self.get_monthly_usage(db, user_id)

        # Calculate reset date (first of next month)
        now = datetime.now(timezone.utc)
        if now.month == 12:
            resets_at = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            resets_at = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

        return UsageInfo(
            used=used,
            limit=subscription.monthly_limit,
            plan=subscription.plan_type,
            resets_at=resets_at,
            can_generate=used < subscription.monthly_limit,
        )

    async def check_can_generate(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> tuple[bool, int, int]:
        """
        Check if user can generate a new speech.

        Args:
            db: Database session
            user_id: The user's ID

        Returns:
            Tuple of (can_generate, used_count, limit)
        """
        usage = await self.get_usage_info(db, user_id)
        return (usage.can_generate, usage.used, usage.limit)


# Singleton instance
_usage_service: Optional[UsageService] = None


def get_usage_service() -> UsageService:
    """Get a UsageService instance."""
    global _usage_service
    if _usage_service is None:
        _usage_service = UsageService()
    return _usage_service

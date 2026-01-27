"""
Upgrade Interest Service

Handles tracking user interest in paid plans for demand validation.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UpgradeInterest as UpgradeInterestModel

logger = logging.getLogger(__name__)


class UpgradeInterestService:
    """Service for managing upgrade interest registrations."""

    async def get_interest(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> Optional[UpgradeInterestModel]:
        """
        Check if user has already registered interest.

        Args:
            db: Database session
            user_id: The user's ID

        Returns:
            UpgradeInterest record if exists, None otherwise
        """
        stmt = select(UpgradeInterestModel).where(
            UpgradeInterestModel.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def register_interest(
        self,
        db: AsyncSession,
        user_id: str,
        email: str,
    ) -> UpgradeInterestModel:
        """
        Register user's interest in upgrading.

        If user already registered, returns existing record.

        Args:
            db: Database session
            user_id: The user's ID
            email: The user's email

        Returns:
            UpgradeInterest record
        """
        # Check if already registered
        existing = await self.get_interest(db, user_id)
        if existing:
            logger.info(f"User {user_id[:8]}... already registered interest")
            return existing

        # Create new interest record
        interest = UpgradeInterestModel(
            user_id=user_id,
            email=email,
        )
        db.add(interest)
        await db.commit()
        await db.refresh(interest)

        logger.info(f"Registered upgrade interest for user {user_id[:8]}... ({email})")
        return interest


# Singleton instance
_upgrade_interest_service: Optional[UpgradeInterestService] = None


def get_upgrade_interest_service() -> UpgradeInterestService:
    """Get an UpgradeInterestService instance."""
    global _upgrade_interest_service
    if _upgrade_interest_service is None:
        _upgrade_interest_service = UpgradeInterestService()
    return _upgrade_interest_service

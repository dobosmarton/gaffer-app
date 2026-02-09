"""
Hype Storage Service

Handles persistence of hype records (generated text and audio) in the database
and audio file storage in Supabase Storage.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import HypeRecord as HypeRecordModel
from app.models import CalendarEvent as CalendarEventModel
from app.services.supabase_client import get_supabase_client
from app.types import HypeStatus, ManagerStyle

logger = logging.getLogger(__name__)


class HypeStorageError(Exception):
    """Base exception for hype storage operations."""

    pass


@dataclass(frozen=True, slots=True)
class HypeRecord:
    """Represents a stored hype record."""

    id: str
    user_id: str
    calendar_event_id: Optional[str]
    google_event_id: Optional[str]
    event_title: str
    event_time: datetime
    manager_style: ManagerStyle
    hype_text: Optional[str]
    audio_text: Optional[str]
    audio_url: Optional[str]
    status: HypeStatus
    created_at: datetime
    updated_at: datetime


class HypeStorageService:
    """Service for managing hype record persistence."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Keep Supabase only for storage operations
        self.supabase = get_supabase_client(settings)

    async def _get_calendar_event_id(
        self, db: AsyncSession, user_id: str, google_event_id: str
    ) -> Optional[str]:
        """Look up our internal calendar_event_id from a google_event_id."""
        try:
            stmt = select(CalendarEventModel.id).where(
                and_(
                    CalendarEventModel.user_id == user_id,
                    CalendarEventModel.google_event_id == google_event_id,
                    CalendarEventModel.is_deleted == False,
                )
            )
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            return str(row) if row else None
        except SQLAlchemyError as e:
            logger.warning(f"Failed to look up calendar_event_id: {e}")
            return None

    async def create_hype_record(
        self,
        db: AsyncSession,
        user_id: str,
        event_title: str,
        event_time: datetime,
        manager_style: str,
        google_event_id: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
    ) -> HypeRecord:
        """
        Create a new hype record with pending status.

        Args:
            db: Database session
            user_id: The user's ID
            event_title: Title of the event
            event_time: Start time of the event
            manager_style: Manager style for the hype
            google_event_id: Google Calendar event ID
            calendar_event_id: Our internal calendar event ID

        Returns:
            The created HypeRecord
        """
        now = datetime.now(timezone.utc)

        # Look up calendar_event_id from google_event_id if not provided
        if google_event_id and not calendar_event_id:
            calendar_event_id = await self._get_calendar_event_id(db, user_id, google_event_id)
            if calendar_event_id:
                logger.info(f"Found calendar_event_id {calendar_event_id[:8]}... for google_event_id {google_event_id[:8]}...")

        try:
            record = HypeRecordModel(
                user_id=user_id,
                event_title=event_title,
                event_time=event_time,
                manager_style=manager_style,
                status="pending",
                google_event_id=google_event_id,
                calendar_event_id=calendar_event_id,
                created_at=now,
                updated_at=now,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            logger.info(f"Created hype record {record.id} for user {user_id[:8]}...")
            return self._model_to_record(record)
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to create hype record: {e}")
            raise HypeStorageError(f"Failed to create hype record: {e}")

    async def update_with_text(
        self,
        db: AsyncSession,
        record_id: str,
        hype_text: str,
        audio_text: str,
    ) -> HypeRecord:
        """
        Update a hype record with generated text.

        Args:
            db: Database session
            record_id: The hype record ID
            hype_text: Clean text for display
            audio_text: Text with emotion tags for TTS

        Returns:
            The updated HypeRecord
        """
        now = datetime.now(timezone.utc)

        try:
            stmt = (
                update(HypeRecordModel)
                .where(HypeRecordModel.id == record_id)
                .values(
                    hype_text=hype_text,
                    audio_text=audio_text,
                    status="text_ready",
                    updated_at=now,
                )
                .returning(HypeRecordModel)
            )
            result = await db.execute(stmt)
            await db.commit()
            record = result.scalar_one()
            logger.info(f"Updated hype record {record_id} with text")
            return self._model_to_record(record)
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to update hype record with text: {e}")
            raise HypeStorageError(f"Failed to update hype record: {e}")

    async def upload_audio(
        self,
        db: AsyncSession,
        record_id: str,
        user_id: str,
        audio_data: bytes,
    ) -> str:
        """
        Upload audio to Supabase Storage and update the record.

        Args:
            db: Database session
            record_id: The hype record ID
            user_id: The user's ID
            audio_data: Raw audio bytes (MP3)

        Returns:
            The public URL of the uploaded audio
        """
        now = datetime.now(timezone.utc)
        file_path = f"{user_id}/{record_id}.mp3"

        try:
            # Upload to Supabase Storage
            self.supabase.storage.from_("hype-audio").upload(
                file_path,
                audio_data,
                file_options={"content-type": "audio/mpeg"},
            )

            # Get public URL
            audio_url = self.supabase.storage.from_("hype-audio").get_public_url(
                file_path
            )

            # Update record with audio URL using SQLAlchemy
            stmt = (
                update(HypeRecordModel)
                .where(HypeRecordModel.id == record_id)
                .values(
                    audio_url=audio_url,
                    status="audio_ready",
                    updated_at=now,
                )
            )
            await db.execute(stmt)
            await db.commit()

            logger.info(f"Uploaded audio for hype record {record_id}")
            return audio_url

        except (SQLAlchemyError, OSError) as e:
            logger.error(f"Failed to upload audio: {e}")
            # Update status to error
            try:
                stmt = (
                    update(HypeRecordModel)
                    .where(HypeRecordModel.id == record_id)
                    .values(
                        status="error",
                        updated_at=now,
                    )
                )
                await db.execute(stmt)
                await db.commit()
            except SQLAlchemyError:
                await db.rollback()
            raise HypeStorageError(f"Failed to upload audio: {e}")

    async def update_audio_url(
        self,
        db: AsyncSession,
        record_id: str,
        audio_url: str,
    ) -> HypeRecord:
        """
        Update a hype record with an audio URL (for cases where audio is stored externally).

        Args:
            db: Database session
            record_id: The hype record ID
            audio_url: URL to the audio file

        Returns:
            The updated HypeRecord
        """
        now = datetime.now(timezone.utc)

        try:
            stmt = (
                update(HypeRecordModel)
                .where(HypeRecordModel.id == record_id)
                .values(
                    audio_url=audio_url,
                    status="audio_ready",
                    updated_at=now,
                )
                .returning(HypeRecordModel)
            )
            result = await db.execute(stmt)
            await db.commit()
            record = result.scalar_one()
            logger.info(f"Updated hype record {record_id} with audio URL")
            return self._model_to_record(record)
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to update hype record with audio: {e}")
            raise HypeStorageError(f"Failed to update hype record: {e}")

    async def get_hype_record(
        self, db: AsyncSession, record_id: str
    ) -> Optional[HypeRecord]:
        """
        Get a specific hype record by ID.

        Args:
            db: Database session
            record_id: The hype record ID

        Returns:
            The HypeRecord or None if not found
        """
        try:
            stmt = select(HypeRecordModel).where(HypeRecordModel.id == record_id)
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()
            return self._model_to_record(record) if record else None
        except SQLAlchemyError as e:
            logger.warning(f"Failed to get hype record {record_id}: {e}")
            return None

    async def get_hype_history(
        self,
        db: AsyncSession,
        user_id: str,
        google_event_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[HypeRecord]:
        """
        Get hype history for a user.

        Args:
            db: Database session
            user_id: The user's ID
            google_event_id: Optional filter by Google event ID
            limit: Maximum number of records to return

        Returns:
            List of HypeRecords, newest first
        """
        conditions = [HypeRecordModel.user_id == user_id]
        if google_event_id:
            conditions.append(HypeRecordModel.google_event_id == google_event_id)

        stmt = (
            select(HypeRecordModel)
            .where(and_(*conditions))
            .order_by(HypeRecordModel.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        records = result.scalars().all()

        return [self._model_to_record(r) for r in records]

    async def get_latest_hype_for_event(
        self,
        db: AsyncSession,
        user_id: str,
        google_event_id: str,
    ) -> Optional[HypeRecord]:
        """
        Get the most recent hype record for a specific event.

        Args:
            db: Database session
            user_id: The user's ID
            google_event_id: Google Calendar event ID

        Returns:
            The most recent HypeRecord or None
        """
        records = await self.get_hype_history(
            db, user_id, google_event_id=google_event_id, limit=1
        )
        return records[0] if records else None

    def _model_to_record(self, model: HypeRecordModel) -> HypeRecord:
        """Convert a SQLAlchemy model to a HypeRecord dataclass."""
        return HypeRecord(
            id=str(model.id),
            user_id=str(model.user_id),
            calendar_event_id=str(model.calendar_event_id) if model.calendar_event_id else None,
            google_event_id=model.google_event_id,
            event_title=model.event_title,
            event_time=model.event_time,
            manager_style=model.manager_style,
            hype_text=model.hype_text,
            audio_text=model.audio_text,
            audio_url=model.audio_url,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


def get_hype_storage_service() -> HypeStorageService:
    """Get a HypeStorageService instance."""
    settings = get_settings()
    return HypeStorageService(settings)

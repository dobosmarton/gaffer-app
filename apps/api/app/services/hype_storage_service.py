"""
Hype Storage Service

Handles persistence of hype records (generated text and audio) in the database
and audio file storage in Supabase Storage.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.config import Settings, get_settings
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class HypeStorageError(Exception):
    """Base exception for hype storage operations."""

    pass


@dataclass
class HypeRecord:
    """Represents a stored hype record."""

    id: str
    user_id: str
    calendar_event_id: Optional[str]
    google_event_id: Optional[str]
    event_title: str
    event_time: datetime
    manager_style: str
    hype_text: Optional[str]
    audio_text: Optional[str]
    audio_url: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class HypeStorageService:
    """Service for managing hype record persistence."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.supabase = get_supabase_client(settings)

    async def _get_calendar_event_id(
        self, user_id: str, google_event_id: str
    ) -> Optional[str]:
        """Look up our internal calendar_event_id from a google_event_id."""
        try:
            response = (
                self.supabase.table("calendar_events")
                .select("id")
                .eq("user_id", user_id)
                .eq("google_event_id", google_event_id)
                .eq("is_deleted", False)
                .single()
                .execute()
            )
            return response.data["id"] if response.data else None
        except Exception:
            return None

    async def create_hype_record(
        self,
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
            user_id: The user's ID
            event_title: Title of the event
            event_time: Start time of the event
            manager_style: Manager style for the hype
            google_event_id: Google Calendar event ID
            calendar_event_id: Our internal calendar event ID

        Returns:
            The created HypeRecord
        """
        now = datetime.now(timezone.utc).isoformat()

        # Look up calendar_event_id from google_event_id if not provided
        if google_event_id and not calendar_event_id:
            calendar_event_id = await self._get_calendar_event_id(user_id, google_event_id)
            if calendar_event_id:
                logger.info(f"Found calendar_event_id {calendar_event_id[:8]}... for google_event_id {google_event_id[:8]}...")

        data = {
            "user_id": user_id,
            "event_title": event_title,
            "event_time": event_time.isoformat(),
            "manager_style": manager_style,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }

        if google_event_id:
            data["google_event_id"] = google_event_id
        if calendar_event_id:
            data["calendar_event_id"] = calendar_event_id

        try:
            response = self.supabase.table("hype_records").insert(data).execute()
            row = response.data[0]
            logger.info(f"Created hype record {row['id']} for user {user_id[:8]}...")
            return self._row_to_record(row)
        except Exception as e:
            logger.error(f"Failed to create hype record: {e}")
            raise HypeStorageError(f"Failed to create hype record: {e}")

    async def update_with_text(
        self,
        record_id: str,
        hype_text: str,
        audio_text: str,
    ) -> HypeRecord:
        """
        Update a hype record with generated text.

        Args:
            record_id: The hype record ID
            hype_text: Clean text for display
            audio_text: Text with emotion tags for TTS

        Returns:
            The updated HypeRecord
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            response = (
                self.supabase.table("hype_records")
                .update({
                    "hype_text": hype_text,
                    "audio_text": audio_text,
                    "status": "text_ready",
                    "updated_at": now,
                })
                .eq("id", record_id)
                .execute()
            )
            row = response.data[0]
            logger.info(f"Updated hype record {record_id} with text")
            return self._row_to_record(row)
        except Exception as e:
            logger.error(f"Failed to update hype record with text: {e}")
            raise HypeStorageError(f"Failed to update hype record: {e}")

    async def upload_audio(
        self,
        record_id: str,
        user_id: str,
        audio_data: bytes,
    ) -> str:
        """
        Upload audio to Supabase Storage and update the record.

        Args:
            record_id: The hype record ID
            user_id: The user's ID
            audio_data: Raw audio bytes (MP3)

        Returns:
            The public URL of the uploaded audio
        """
        now = datetime.now(timezone.utc).isoformat()
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

            # Update record with audio URL
            self.supabase.table("hype_records").update({
                "audio_url": audio_url,
                "status": "audio_ready",
                "updated_at": now,
            }).eq("id", record_id).execute()

            logger.info(f"Uploaded audio for hype record {record_id}")
            return audio_url

        except Exception as e:
            logger.error(f"Failed to upload audio: {e}")
            # Update status to error
            self.supabase.table("hype_records").update({
                "status": "error",
                "updated_at": now,
            }).eq("id", record_id).execute()
            raise HypeStorageError(f"Failed to upload audio: {e}")

    async def update_audio_url(
        self,
        record_id: str,
        audio_url: str,
    ) -> HypeRecord:
        """
        Update a hype record with an audio URL (for cases where audio is stored externally).

        Args:
            record_id: The hype record ID
            audio_url: URL to the audio file

        Returns:
            The updated HypeRecord
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            response = (
                self.supabase.table("hype_records")
                .update({
                    "audio_url": audio_url,
                    "status": "audio_ready",
                    "updated_at": now,
                })
                .eq("id", record_id)
                .execute()
            )
            row = response.data[0]
            logger.info(f"Updated hype record {record_id} with audio URL")
            return self._row_to_record(row)
        except Exception as e:
            logger.error(f"Failed to update hype record with audio: {e}")
            raise HypeStorageError(f"Failed to update hype record: {e}")

    async def get_hype_record(self, record_id: str) -> Optional[HypeRecord]:
        """
        Get a specific hype record by ID.

        Args:
            record_id: The hype record ID

        Returns:
            The HypeRecord or None if not found
        """
        try:
            response = (
                self.supabase.table("hype_records")
                .select("*")
                .eq("id", record_id)
                .single()
                .execute()
            )
            return self._row_to_record(response.data) if response.data else None
        except Exception:
            return None

    async def get_hype_history(
        self,
        user_id: str,
        google_event_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[HypeRecord]:
        """
        Get hype history for a user.

        Args:
            user_id: The user's ID
            google_event_id: Optional filter by Google event ID
            limit: Maximum number of records to return

        Returns:
            List of HypeRecords, newest first
        """
        query = (
            self.supabase.table("hype_records")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
        )

        if google_event_id:
            query = query.eq("google_event_id", google_event_id)

        response = query.execute()

        return [self._row_to_record(row) for row in response.data or []]

    async def get_latest_hype_for_event(
        self,
        user_id: str,
        google_event_id: str,
    ) -> Optional[HypeRecord]:
        """
        Get the most recent hype record for a specific event.

        Args:
            user_id: The user's ID
            google_event_id: Google Calendar event ID

        Returns:
            The most recent HypeRecord or None
        """
        records = await self.get_hype_history(
            user_id, google_event_id=google_event_id, limit=1
        )
        return records[0] if records else None

    def _row_to_record(self, row: dict) -> HypeRecord:
        """Convert a database row to a HypeRecord."""
        return HypeRecord(
            id=row["id"],
            user_id=row["user_id"],
            calendar_event_id=row.get("calendar_event_id"),
            google_event_id=row.get("google_event_id"),
            event_title=row["event_title"],
            event_time=datetime.fromisoformat(
                row["event_time"].replace("Z", "+00:00")
            ),
            manager_style=row["manager_style"],
            hype_text=row.get("hype_text"),
            audio_text=row.get("audio_text"),
            audio_url=row.get("audio_url"),
            status=row["status"],
            created_at=datetime.fromisoformat(
                row["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                row["updated_at"].replace("Z", "+00:00")
            ),
        )


def get_hype_storage_service() -> HypeStorageService:
    """Get a HypeStorageService instance."""
    settings = get_settings()
    return HypeStorageService(settings)

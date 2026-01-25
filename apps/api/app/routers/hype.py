import logging
from datetime import datetime
from typing import Optional

from elevenlabs import ElevenLabs, VoiceSettings
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.routers.auth import get_user_id_from_token
from app.services.database import get_db
from app.services.hype_generator import (
    generate_hype_text,
    sanitize_audio_tags,
    strip_audio_tags,
)
from app.services.hype_storage_service import (
    HypeStorageError,
    HypeStorageService,
    get_hype_storage_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Custom voice IDs for each manager (created via ElevenLabs Voice Design)
MANAGER_VOICE_IDS: dict[str, str] = {
    "ferguson": "P0j68WlVxoVLfmeuIlDe",
    "klopp": "PGbssAP11uFtfjF1cht6",
    "guardiola": "yJTcVhaSn9fh8KNg4zyA",
    "mourinho": "ZhCPijZY63OCwbLO1lJj",
    "bielsa": "fFgsPtiWKktwRqxDvzzZ",
}


class GenerateHypeRequest(BaseModel):
    event_title: str
    event_description: str | None = None
    event_time: str
    manager_style: str = "ferguson"
    google_event_id: str | None = None  # Optional link to calendar event
    persist: bool = True  # Whether to save to database


class GenerateHypeResponse(BaseModel):
    hype_id: str
    hype_text: str   # Clean text for display (tags stripped)
    audio_text: str  # Text with validated tags for TTS
    manager: str
    status: str
    audio_url: str | None = None  # URL if audio was persisted


class AudioRequest(BaseModel):
    text: str
    voice_id: str | None = None
    manager: str | None = None  # Used to select manager-specific voice
    hype_id: str | None = None  # If provided, persist audio to this record


class HypeHistoryItem(BaseModel):
    id: str
    event_title: str
    event_time: datetime
    manager_style: str
    hype_text: str | None
    audio_url: str | None
    status: str
    created_at: datetime


class HypeHistoryResponse(BaseModel):
    records: list[HypeHistoryItem]


@router.post("/generate", response_model=GenerateHypeResponse)
async def generate_hype(
    request: GenerateHypeRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    storage_service: HypeStorageService = Depends(get_hype_storage_service),
):
    """Generate hype text using Claude and optionally persist to database."""
    hype_record = None

    # Create hype record if persisting
    if request.persist:
        try:
            # Parse event time
            event_time = datetime.fromisoformat(
                request.event_time.replace("Z", "+00:00")
            )
            hype_record = await storage_service.create_hype_record(
                db=db,
                user_id=user_id,
                event_title=request.event_title,
                event_time=event_time,
                manager_style=request.manager_style,
                google_event_id=request.google_event_id,
            )
            logger.info(f"Created hype record {hype_record.id} for user {user_id[:8]}...")
        except HypeStorageError as e:
            logger.warning(f"Failed to create hype record, continuing without persistence: {e}")

    # Generate hype text
    raw_text = await generate_hype_text(
        event_title=request.event_title,
        event_description=request.event_description,
        event_time=request.event_time,
        manager_style=request.manager_style,
    )

    hype_text = strip_audio_tags(raw_text)
    audio_text = sanitize_audio_tags(raw_text)

    logger.info(f"[HYPE] Raw text with tags:\n{raw_text}")
    logger.info(f"[HYPE] Sanitized audio text:\n{audio_text}")

    # Update record with text if persisting
    if hype_record:
        try:
            hype_record = await storage_service.update_with_text(
                db=db,
                record_id=hype_record.id,
                hype_text=hype_text,
                audio_text=audio_text,
            )
        except HypeStorageError as e:
            logger.warning(f"Failed to update hype record with text: {e}")

    return GenerateHypeResponse(
        hype_id=hype_record.id if hype_record else "temp-" + str(hash(raw_text))[:8],
        hype_text=hype_text,
        audio_text=audio_text,
        manager=request.manager_style,
        status="text_ready",
    )


@router.post("/audio")
async def generate_audio(
    request: AudioRequest,
    settings: Settings = Depends(get_settings),
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    storage_service: HypeStorageService = Depends(get_hype_storage_service),
):
    """Generate audio from ElevenLabs text-to-speech.

    If hype_id is provided, the audio will be uploaded to storage and the
    record will be updated with the audio URL.
    """
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    # Select voice: explicit voice_id > manager-specific voice > default
    voice_id = request.voice_id
    if not voice_id and request.manager:
        voice_id = MANAGER_VOICE_IDS.get(request.manager)
    voice_id = voice_id or settings.elevenlabs_voice_id

    logger.info(f"[AUDIO] Using voice_id: {voice_id} for manager: {request.manager}")

    # Generate audio using ElevenLabs v3 with audio tag support
    # v3 stability: 0.0=Creative (expressive), 0.5=Natural, 1.0=Robust (flat)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=request.text,
        model_id="eleven_v3",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.5,  # Natural mode for more consistent delivery
            similarity_boost=0.75,  # Keep voice consistent
        ),
    )

    # If hype_id provided, upload to storage
    if request.hype_id and not request.hype_id.startswith("temp-"):
        try:
            # Collect all audio bytes
            audio_bytes = b"".join(audio_stream)

            # Upload to Supabase Storage
            audio_url = await storage_service.upload_audio(
                db=db,
                record_id=request.hype_id,
                user_id=user_id,
                audio_data=audio_bytes,
            )
            logger.info(f"Uploaded audio for hype record {request.hype_id}")

            # Return audio bytes as response (already generated)
            return StreamingResponse(
                iter([audio_bytes]),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline",
                    "Cache-Control": "no-cache",
                    "X-Audio-Url": audio_url,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to upload audio, streaming without persistence: {e}")
            # Regenerate stream since we consumed it
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_id,
                text=request.text,
                model_id="eleven_v3",
                output_format="mp3_44100_128",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                ),
            )

    return StreamingResponse(
        audio_stream,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/history", response_model=HypeHistoryResponse)
async def get_hype_history(
    google_event_id: Optional[str] = None,
    limit: int = 20,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    storage_service: HypeStorageService = Depends(get_hype_storage_service),
):
    """Get hype generation history.

    Optionally filter by Google Calendar event ID.
    """
    records = await storage_service.get_hype_history(
        db=db,
        user_id=user_id,
        google_event_id=google_event_id,
        limit=limit,
    )

    return HypeHistoryResponse(
        records=[
            HypeHistoryItem(
                id=r.id,
                event_title=r.event_title,
                event_time=r.event_time,
                manager_style=r.manager_style,
                hype_text=r.hype_text,
                audio_url=r.audio_url,
                status=r.status,
                created_at=r.created_at,
            )
            for r in records
        ]
    )


@router.get("/{hype_id}", response_model=HypeHistoryItem)
async def get_hype_record(
    hype_id: str,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    storage_service: HypeStorageService = Depends(get_hype_storage_service),
):
    """Get a specific hype record by ID."""
    record = await storage_service.get_hype_record(db, hype_id)

    if not record:
        raise HTTPException(status_code=404, detail="Hype record not found")

    # Verify ownership
    if record.user_id != user_id:
        raise HTTPException(status_code=404, detail="Hype record not found")

    return HypeHistoryItem(
        id=record.id,
        event_title=record.event_title,
        event_time=record.event_time,
        manager_style=record.manager_style,
        hype_text=record.hype_text,
        audio_url=record.audio_url,
        status=record.status,
        created_at=record.created_at,
    )

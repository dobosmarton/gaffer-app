import logging
from datetime import datetime
from typing import Optional

from elevenlabs import ElevenLabs, VoiceSettings
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.rate_limiter import limiter
from app.types import HypeStatus, ManagerStyle
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
from app.services.usage_service import (
    UsageService,
    get_usage_service,
)
from app.services.upgrade_interest_service import (
    UpgradeInterestService,
    get_upgrade_interest_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Custom voice IDs for each manager (created via ElevenLabs Voice Design)
MANAGER_VOICE_IDS: dict[ManagerStyle, str] = {
    "ferguson": "P0j68WlVxoVLfmeuIlDe",
    "klopp": "PGbssAP11uFtfjF1cht6",
    "guardiola": "yJTcVhaSn9fh8KNg4zyA",
    "mourinho": "ZhCPijZY63OCwbLO1lJj",
    "bielsa": "fFgsPtiWKktwRqxDvzzZ",
}


class GenerateHypeRequest(BaseModel):
    event_title: str = Field(..., max_length=500)
    event_description: str | None = Field(None, max_length=5000)
    event_time: str
    manager_style: ManagerStyle = "ferguson"
    google_event_id: str | None = Field(None, max_length=255)
    persist: bool = True  # Whether to save to database


class GenerateHypeResponse(BaseModel):
    hype_id: str
    hype_text: str   # Clean text for display (tags stripped)
    audio_text: str  # Text with validated tags for TTS
    manager: ManagerStyle
    status: HypeStatus
    audio_url: str | None = None  # URL if audio was persisted


class AudioRequest(BaseModel):
    text: str = Field(..., max_length=10000)
    voice_id: str | None = Field(None, max_length=100)
    manager: ManagerStyle | None = None
    hype_id: str | None = Field(None, max_length=100)


class HypeHistoryItem(BaseModel):
    id: str
    event_title: str
    event_time: datetime
    manager_style: ManagerStyle
    hype_text: str | None
    audio_url: str | None
    status: HypeStatus
    created_at: datetime


class HypeHistoryResponse(BaseModel):
    records: list[HypeHistoryItem]


class UsageResponse(BaseModel):
    used: int
    limit: int
    plan: str
    resets_at: datetime
    can_generate: bool


class RegisterInterestRequest(BaseModel):
    email: EmailStr


class InterestStatusResponse(BaseModel):
    registered: bool
    registered_at: datetime | None = None


@router.post("/generate", response_model=GenerateHypeResponse)
@limiter.limit("10/minute")
async def generate_hype(
    request: Request,
    body: GenerateHypeRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    storage_service: HypeStorageService = Depends(get_hype_storage_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Generate hype text using Claude and optionally persist to database."""
    # Check usage limit before generating
    usage = await usage_service.get_usage_info(db, user_id)
    if not usage.can_generate:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Monthly limit reached ({usage.used}/{usage.limit} speeches)",
                "used": usage.used,
                "limit": usage.limit,
                "resets_at": usage.resets_at.isoformat(),
            },
        )

    hype_record = None

    # Create hype record if persisting
    if body.persist:
        try:
            # Parse event time
            event_time = datetime.fromisoformat(
                body.event_time.replace("Z", "+00:00")
            )
            hype_record = await storage_service.create_hype_record(
                db=db,
                user_id=user_id,
                event_title=body.event_title,
                event_time=event_time,
                manager_style=body.manager_style,
                google_event_id=body.google_event_id,
            )
            logger.info(f"Created hype record {hype_record.id} for user {user_id[:8]}...")
        except HypeStorageError as e:
            logger.warning(f"Failed to create hype record, continuing without persistence: {e}")

    # Generate hype text
    raw_text = await generate_hype_text(
        event_title=body.event_title,
        event_description=body.event_description,
        event_time=body.event_time,
        manager_style=body.manager_style,
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
        manager=body.manager_style,
        status="text_ready",
    )


@router.post("/audio")
@limiter.limit("10/minute")
async def generate_audio(
    request: Request,
    body: AudioRequest,
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
    voice_id = body.voice_id
    if not voice_id and body.manager:
        voice_id = MANAGER_VOICE_IDS.get(body.manager)
    voice_id = voice_id or settings.elevenlabs_voice_id

    logger.info(f"[AUDIO] Using voice_id: {voice_id} for manager: {body.manager}")

    # Generate audio using ElevenLabs v3 with audio tag support
    # v3 stability: 0.0=Creative (expressive), 0.5=Natural, 1.0=Robust (flat)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=body.text,
        model_id="eleven_v3",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.5,  # Natural mode for more consistent delivery
            similarity_boost=0.75,  # Keep voice consistent
        ),
    )

    # If hype_id provided, upload to storage
    if body.hype_id and not body.hype_id.startswith("temp-"):
        try:
            # Collect all audio bytes
            audio_bytes = b"".join(audio_stream)

            # Upload to Supabase Storage
            audio_url = await storage_service.upload_audio(
                db=db,
                record_id=body.hype_id,
                user_id=user_id,
                audio_data=audio_bytes,
            )
            logger.info(f"Uploaded audio for hype record {body.hype_id}")

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
        except (HypeStorageError, OSError) as e:
            logger.warning(f"Failed to upload audio, streaming without persistence: {e}")
            # Regenerate stream since we consumed it
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_id,
                text=body.text,
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


@router.get("/usage", response_model=UsageResponse)
async def get_usage_status(
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Get current usage status for the authenticated user."""
    usage = await usage_service.get_usage_info(db, user_id)
    return UsageResponse(
        used=usage.used,
        limit=usage.limit,
        plan=usage.plan,
        resets_at=usage.resets_at,
        can_generate=usage.can_generate,
    )


@router.post("/interest", response_model=InterestStatusResponse)
async def register_upgrade_interest(
    request: RegisterInterestRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    interest_service: UpgradeInterestService = Depends(get_upgrade_interest_service),
):
    """Register user's interest in upgrading to a paid plan."""
    interest = await interest_service.register_interest(
        db=db,
        user_id=user_id,
        email=request.email,
    )
    return InterestStatusResponse(
        registered=True,
        registered_at=interest.created_at,
    )


@router.get("/interest/status", response_model=InterestStatusResponse)
async def get_interest_status(
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    interest_service: UpgradeInterestService = Depends(get_upgrade_interest_service),
):
    """Check if user has already registered interest in upgrading."""
    interest = await interest_service.get_interest(db=db, user_id=user_id)
    if interest:
        return InterestStatusResponse(
            registered=True,
            registered_at=interest.created_at,
        )
    return InterestStatusResponse(registered=False)


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

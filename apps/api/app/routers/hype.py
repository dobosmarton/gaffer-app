from uuid import uuid4

from elevenlabs import ElevenLabs, VoiceSettings
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.hype_generator import (
    generate_hype_text,
    sanitize_audio_tags,
    strip_audio_tags,
)

router = APIRouter()


class GenerateHypeRequest(BaseModel):
    event_title: str
    event_description: str | None = None
    event_time: str
    manager_style: str = "ferguson"


class GenerateHypeResponse(BaseModel):
    hype_id: str
    hype_text: str   # Clean text for display (tags stripped)
    audio_text: str  # Text with validated tags for TTS
    manager: str
    status: str


class AudioRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.post("/generate", response_model=GenerateHypeResponse)
async def generate_hype(request: GenerateHypeRequest):
    """Generate hype text using Claude."""
    raw_text = await generate_hype_text(
        event_title=request.event_title,
        event_description=request.event_description,
        event_time=request.event_time,
        manager_style=request.manager_style,
    )

    audio_text = sanitize_audio_tags(raw_text)
    print(f"\n[HYPE] Raw text with tags:\n{raw_text}")
    print(f"\n[HYPE] Sanitized audio text:\n{audio_text}\n")

    return GenerateHypeResponse(
        hype_id=str(uuid4()),
        hype_text=strip_audio_tags(raw_text),  # Clean for display
        audio_text=audio_text,                  # With validated tags for TTS
        manager=request.manager_style,
        status="text_ready",
    )


@router.post("/audio")
async def generate_audio(
    request: AudioRequest,
    settings: Settings = Depends(get_settings),
):
    """Stream audio from ElevenLabs text-to-speech."""
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    voice_id = request.voice_id or settings.elevenlabs_voice_id

    # Generate audio stream using ElevenLabs v3 with audio tag support
    # v3 stability: 0.0=Creative (expressive), 0.5=Natural, 1.0=Robust (flat)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=request.text,
        model_id="eleven_v3",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.0,          # Creative mode for max expressiveness
            similarity_boost=0.75,  # Keep voice consistent
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

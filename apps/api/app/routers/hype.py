from uuid import uuid4

from elevenlabs import ElevenLabs
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.hype_generator import generate_hype_text

router = APIRouter()


class GenerateHypeRequest(BaseModel):
    event_title: str
    event_description: str | None = None
    event_time: str
    manager_style: str = "ferguson"


class GenerateHypeResponse(BaseModel):
    hype_id: str
    hype_text: str
    manager: str
    status: str


class AudioRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.post("/generate", response_model=GenerateHypeResponse)
async def generate_hype(request: GenerateHypeRequest):
    """Generate hype text using Claude."""
    hype_text = await generate_hype_text(
        event_title=request.event_title,
        event_description=request.event_description,
        event_time=request.event_time,
        manager_style=request.manager_style,
    )

    return GenerateHypeResponse(
        hype_id=str(uuid4()),
        hype_text=hype_text,
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

    # Generate audio stream using the SDK
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=request.text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    return StreamingResponse(
        audio_stream,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-cache",
        },
    )

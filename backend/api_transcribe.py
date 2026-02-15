from fastapi import APIRouter, Query
from backend.transcription_service import transcribe_with_diarization, get_quota_info
from backend.groq_transcription import transcribe_with_groq, get_groq_quota

router = APIRouter()

@router.post("/api/transcribe")
async def transcribe_call(
    audio_url: str,
    provider: str = Query("whisperx", description="whisperx or groq"),
    num_speakers: int = 2
):
    """Транскрибация звонка"""
    if provider == "groq":
        return transcribe_with_groq(audio_url)
    else:
        return transcribe_with_diarization(audio_url, num_speakers)

@router.get("/api/transcribe/quota")
async def quota_info(provider: str = Query("whisperx")):
    if provider == "groq":
        return get_groq_quota()
    else:
        return get_quota_info()

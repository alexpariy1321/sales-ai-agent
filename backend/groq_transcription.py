import os
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_with_groq(audio_url: str) -> dict:
    """Транскрибация через Groq Whisper Large V3"""
    temp_path = None
    
    try:
        print("📥 Скачиваем аудио...")
        response = requests.get(audio_url, timeout=60)
        
        if response.status_code != 200:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
        
        temp_path = "/tmp/groq_call.mp3"
        with open(temp_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ {len(response.content)/1024/1024:.2f} MB")
        print("🚀 Groq Whisper транскрибирует...")
        
        with open(temp_path, "rb") as audio:
            transcription = groq_client.audio.transcriptions.create(
                file=audio,
                model="whisper-large-v3-turbo",
                language="ru",
                response_format="verbose_json",
                temperature=0.0
            )
        
        os.remove(temp_path)
        
        segments = []
        for seg in (transcription.segments or []):
            start = seg.start
            segments.append({
                "speaker": "Неизвестно (без диаризации)",
                "time": f"{int(start//60):02d}:{int(start%60):02d}",
                "text": seg.text
            })
        
        full_transcript = "\n".join([
            f"[{s['time']}] {s['text']}" for s in segments
        ])
        
        print(f"✅ Готово! {len(segments)} сегментов")
        
        return {
            "status": "success",
            "transcript": full_transcript,
            "segments": segments,
            "speakers_map": {"Неизвестно": "Groq не поддерживает диаризацию"},
            "stats": {
                "total_segments": len(segments),
                "duration": f"{transcription.duration:.1f}s",
                "provider": "Groq Whisper Large V3 Turbo"
            }
        }
        
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def get_groq_quota():
    return {
        "provider": "Groq",
        "model": "whisper-large-v3-turbo",
        "tier": "Free",
        "limits": {
            "requests_per_day": 14400,
            "requests_per_minute": 30
        },
        "features": ["Транскрибация", "Временные метки", "Работает в РФ"],
        "status": "✅ Работает"
    }

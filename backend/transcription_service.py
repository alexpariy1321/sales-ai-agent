import os
import requests
import whisperx
import torch
import gc
import subprocess
from pyannote.audio import Pipeline
from dotenv import load_dotenv

load_dotenv()

_whisper_model = None
_diarize_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("Загружаем Whisper MEDIUM (точнее base)...")
        _whisper_model = whisperx.load_model(
            "medium",  # ← Было base, теперь medium
            device="cpu",
            compute_type="int8",
            language="ru"
        )
        print("✅ Whisper medium готов")
    return _whisper_model

def get_diarize_model():
    global _diarize_model
    if _diarize_model is None:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN не найден")
        
        print("Загружаем pyannote диаризацию 3.1...")
        _diarize_model = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        _diarize_model.to(torch.device("cpu"))
        print("✅ Diarization готов")
    return _diarize_model

def fix_audio_with_ffmpeg(input_path: str, output_path: str) -> bool:
    """Конвертирует MP3 → WAV через ffmpeg"""
    try:
        subprocess.run([
            "ffmpeg",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-y",
            output_path
        ], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def transcribe_with_diarization(audio_url: str, num_speakers: int = 2) -> dict:
    temp_mp3_path = None
    temp_wav_path = None
    
    try:
        print(f"📥 Скачиваем аудио...")
        response = requests.get(audio_url, timeout=60)
        
        if response.status_code != 200:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
        
        temp_mp3_path = "/tmp/temp_call.mp3"
        temp_wav_path = "/tmp/temp_call.wav"
        
        with open(temp_mp3_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ {len(response.content)/1024/1024:.2f} MB")
        
        # Конвертируем через ffmpeg
        print("🔧 Конвертируем MP3→WAV...")
        if not fix_audio_with_ffmpeg(temp_mp3_path, temp_wav_path):
            return {"status": "error", "error": "Ошибка ffmpeg"}
        
        # Загружаем WAV
        print("🎧 Загрузка...")
        audio = whisperx.load_audio(temp_wav_path)
        
        duration = len(audio) / 16000
        print(f"⏱️  Длительность: {duration:.1f}с")
        
        # Транскрибация (medium модель)
        print("📝 Whisper MEDIUM транскрибация...")
        model = get_whisper_model()
        result = model.transcribe(audio, batch_size=8)  # batch=8 для medium
        
        # Диаризация для длинных звонков
        use_diarization = duration > 20
        
        if use_diarization:
            try:
                print("👥 Pyannote диаризация (2 спикера)...")
                diarize_model = get_diarize_model()
                
                diarize_result = diarize_model(
                    temp_wav_path,
                    min_speakers=num_speakers,
                    max_speakers=num_speakers
                )
                
                # Присваиваем спикеров к сегментам
                segments = []
                for seg in result.get("segments", []):
                    start = seg.get("start", 0)
                    end = seg.get("end", start + 1)
                    text = seg.get("text", "").strip()
                    
                    # Находим спикера по временной метке
                    speaker = "UNKNOWN"
                    max_overlap = 0
                    
                    for turn, _, spk in diarize_result.itertracks(yield_label=True):
                        # Вычисляем пересечение сегментов
                        overlap_start = max(start, turn.start)
                        overlap_end = min(end, turn.end)
                        overlap = max(0, overlap_end - overlap_start)
                        
                        if overlap > max_overlap:
                            max_overlap = overlap
                            speaker = spk
                    
                    if text:
                        time_str = f"{int(start // 60):02d}:{int(start % 60):02d}"
                        segments.append({
                            "speaker": speaker,
                            "time": time_str,
                            "text": text
                        })
                
                print(f"✅ Диаризация успешна!")
                
            except Exception as e:
                print(f"⚠️  Диаризация не удалась: {e}")
                use_diarization = False
        
        # Без диаризации
        if not use_diarization:
            segments = []
            for seg in result.get("segments", []):
                start = seg.get("start", 0)
                text = seg.get("text", "").strip()
                
                if text:
                    time_str = f"{int(start // 60):02d}:{int(start % 60):02d}"
                    segments.append({
                        "speaker": "Неизвестно",
                        "time": time_str,
                        "text": text
                    })
        
        # Формируем транскрипт
        full_transcript = []
        for seg in segments:
            full_transcript.append(f"[{seg['time']}] {seg['speaker']}: {seg['text']}")
        
        # Роли спикеров
        speakers_map = {}
        unique_speakers = list(set(seg["speaker"] for seg in segments))
        
        if use_diarization:
            unique_speakers = [s for s in unique_speakers if s != "UNKNOWN"]
            if len(unique_speakers) >= 1:
                speakers_map[unique_speakers[0]] = "Менеджер"
            if len(unique_speakers) >= 2:
                speakers_map[unique_speakers[1]] = "Клиент"
        else:
            speakers_map["Неизвестно"] = "Звонок короткий" if duration <= 20 else "Ошибка диаризации"
        
        # Очистка
        del audio
        gc.collect()
        
        for path in [temp_mp3_path, temp_wav_path]:
            if path and os.path.exists(path):
                os.remove(path)
        
        print(f"✅ Готово! {len(segments)} сегментов")
        
        return {
            "status": "success",
            "transcript": "\n".join(full_transcript),
            "segments": segments,
            "speakers_map": speakers_map,
            "stats": {
                "total_segments": len(segments),
                "speakers_detected": len(unique_speakers),
                "duration": f"{duration:.1f}s",
                "diarization_used": use_diarization,
                "model": "whisper-medium + pyannote-3.1"
            }
        }
        
    except Exception as e:
        for path in [temp_mp3_path, temp_wav_path]:
            if path and os.path.exists(path):
                os.remove(path)
        
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def get_quota_info():
    return {
        "provider": "WhisperX Medium + pyannote (локально)",
        "tier": "Unlimited",
        "model": "whisper-medium + speaker-diarization-3.1",
        "device": "CPU (int8)",
        "note": "Medium точнее base, диаризация >20 сек",
        "status": "✅ Готов"
    }

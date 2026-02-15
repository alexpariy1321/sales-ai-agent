# Применяем патч ДО импорта whisperx
from backend.torch_patch import patched_load
import torch
torch.load = patched_load

import whisperx
from pyannote.audio import Pipeline
import gc
import os
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()

class FastTranscriber:
    """Оптимизированный транскрайбер с диаризацией через pyannote"""
    
    def __init__(self, model_name="tiny", device="cpu"):
        self.device = device
        self.model_name = model_name
        
        # Ищем токен
        self.hf_token = (
            os.getenv("HF_TOKEN") or 
            os.getenv("HUGGINGFACE_TOKEN") or 
            os.getenv("HFTOKEN")
        )
        
        print(f"🚀 Загружаем WhisperX модель '{model_name}'...")
        self.model = whisperx.load_model(
            model_name, 
            device=device, 
            compute_type="int8",
            language="ru"
        )
        
        print("🎯 Загружаем align модель для русского...")
        self.align_model, self.align_metadata = whisperx.load_align_model(
            language_code="ru", 
            device=device
        )
        
        print("👥 Загружаем diarization модель...")
        if self.hf_token:
            try:
                print(f"   Токен найден: {self.hf_token[:15]}...")
                # Используем pyannote напрямую
                self.diarize_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
                self.diarize_model.to(torch.device(device))
                print("   ✅ Диаризация включена!")
            except Exception as e:
                print(f"   ⚠️  Ошибка загрузки диаризации: {str(e)[:100]}")
                self.diarize_model = None
        else:
            self.diarize_model = None
            print("   ⚠️  HF_TOKEN не найден в .env")
        
        print("✅ Все модели загружены!\n")
    
    def transcribe_with_speakers(self, audio_path: str) -> dict:
        """
        Быстрая транскрибация с диаризацией
        """
        try:
            # 1. Загружаем аудио
            audio = whisperx.load_audio(audio_path)
            
            # 2. Транскрибация
            result = self.model.transcribe(audio, batch_size=16)
            
            # 3. Align
            result = whisperx.align(
                result["segments"], 
                self.align_model, 
                self.align_metadata, 
                audio, 
                self.device,
                return_char_alignments=False
            )
            
            # 4. Диаризация через pyannote
            if self.diarize_model:
                try:
                    from pyannote.core import Segment
                    import numpy as np
                    
                    # Конвертируем аудио для pyannote
                    audio_tensor = torch.from_numpy(audio).unsqueeze(0)
                    waveform = {
                        "waveform": audio_tensor,
                        "sample_rate": 16000
                    }
                    
                    # Запускаем диаризацию
                    diarization = self.diarize_model(waveform)
                    
                    # Привязываем спикеров к словам
                    for segment in result["segments"]:
                        segment_start = segment["start"]
                        segment_end = segment["end"]
                        
                        # Находим доминирующего спикера в этом сегменте
                        speakers_in_segment = []
                        for turn, _, speaker in diarization.itertracks(yield_label=True):
                            if turn.start < segment_end and turn.end > segment_start:
                                overlap = min(turn.end, segment_end) - max(turn.start, segment_start)
                                speakers_in_segment.append((speaker, overlap))
                        
                        if speakers_in_segment:
                            # Берем спикера с максимальным временем в сегменте
                            dominant_speaker = max(speakers_in_segment, key=lambda x: x[1])[0]
                            segment["speaker"] = f"SPEAKER_{dominant_speaker}"
                        else:
                            segment["speaker"] = "SPEAKER_00"
                    
                except Exception as e:
                    print(f"⚠️  Диаризация не сработала: {str(e)[:80]}")
                    # Присваиваем всем SPEAKER_00
                    for segment in result["segments"]:
                        segment["speaker"] = "SPEAKER_00"
            else:
                # Без диаризации - все SPEAKER_00
                for segment in result["segments"]:
                    segment["speaker"] = "SPEAKER_00"
            
            # 5. Форматируем результат
            full_text = " ".join([seg.get("text", "") for seg in result["segments"]])
            
            speakers_text = []
            for seg in result["segments"]:
                speaker = seg.get("speaker", "SPEAKER_00")
                text = seg.get("text", "")
                if text.strip():
                    speakers_text.append({
                        "speaker": speaker,
                        "text": text.strip(),
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0)
                    })
            
            return {
                "transcript": full_text.strip(),
                "speakers": speakers_text,
                "duration": audio.shape[0] / 16000,
                "num_speakers": len(set([s['speaker'] for s in speakers_text])),
                "status": "success"
            }
        except Exception as e:
            return {
                "transcript": "",
                "speakers": [],
                "duration": 0,
                "num_speakers": 0,
                "status": "error",
                "error": str(e)
            }
    
    def cleanup(self):
        """Освобождаем память"""
        try:
            del self.model
            del self.align_model
            if self.diarize_model:
                del self.diarize_model
            gc.collect()
        except:
            pass

def transcribe_audio(audio_path: str) -> dict:
    """Обертка для быстрого вызова"""
    transcriber = FastTranscriber(model_name="tiny")
    result = transcriber.transcribe_with_speakers(audio_path)
    transcriber.cleanup()
    return result

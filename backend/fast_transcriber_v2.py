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
    """Оптимизированный транскрайбер для звонков (всегда 2 спикера)"""
    
    def __init__(self, model_name="tiny", device="cpu"):
        self.device = device
        self.model_name = model_name
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
        
        print("👥 Загружаем diarization модель (фиксировано 2 спикера)...")
        if self.hf_token:
            try:
                self.diarize_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
                self.diarize_model.to(torch.device(device))
                print("   ✅ Диаризация включена!")
            except Exception as e:
                print(f"   ⚠️  Диаризация отключена: {str(e)[:80]}")
                self.diarize_model = None
        else:
            self.diarize_model = None
            print("   ⚠️  HF_TOKEN не найден")
        
        print("✅ Готово!\n")
    
    def transcribe_with_speakers(self, audio_path: str) -> dict:
        """Транскрибация с диаризацией (2 спикера: менеджер + клиент)"""
        try:
            audio = whisperx.load_audio(audio_path)
            
            # Транскрибация
            result = self.model.transcribe(audio, batch_size=16)
            
            # Align
            result = whisperx.align(
                result["segments"], 
                self.align_model, 
                self.align_metadata, 
                audio, 
                self.device,
                return_char_alignments=False
            )
            
            # Диаризация (если доступна)
            if self.diarize_model:
                try:
                    audio_tensor = torch.from_numpy(audio).unsqueeze(0)
                    waveform = {"waveform": audio_tensor, "sample_rate": 16000}
                    
                    # Принудительно 2 спикера (min=2, max=2)
                    diarization = self.diarize_model(
                        waveform,
                        min_speakers=2,
                        max_speakers=2
                    )
                    
                    # Маппинг спикеров: SPEAKER_00 = менеджер, SPEAKER_01 = клиент
                    for segment in result["segments"]:
                        segment_start = segment["start"]
                        segment_end = segment["end"]
                        
                        speakers_in_segment = []
                        for turn, _, speaker in diarization.itertracks(yield_label=True):
                            if turn.start < segment_end and turn.end > segment_start:
                                overlap = min(turn.end, segment_end) - max(turn.start, segment_start)
                                speakers_in_segment.append((speaker, overlap))
                        
                        if speakers_in_segment:
                            dominant_speaker = max(speakers_in_segment, key=lambda x: x[1])[0]
                            # Нормализуем имена спикеров
                            speaker_num = 0 if "0" in str(dominant_speaker) else 1
                            segment["speaker"] = f"SPEAKER_{speaker_num:02d}"
                        else:
                            segment["speaker"] = "SPEAKER_00"
                
                except Exception as e:
                    print(f"⚠️  Диаризация пропущена: {str(e)[:60]}")
                    for segment in result["segments"]:
                        segment["speaker"] = "SPEAKER_00"
            else:
                for segment in result["segments"]:
                    segment["speaker"] = "SPEAKER_00"
            
            # Форматируем результат
            full_text = " ".join([seg.get("text", "") for seg in result["segments"]])
            
            speakers_text = []
            current_speaker = None
            current_text = []
            current_start = 0
            
            # Объединяем последовательные реплики одного спикера
            for seg in result["segments"]:
                speaker = seg.get("speaker", "SPEAKER_00")
                text = seg.get("text", "").strip()
                
                if not text:
                    continue
                
                if speaker != current_speaker:
                    # Сохраняем предыдущую реплику
                    if current_text:
                        speakers_text.append({
                            "speaker": current_speaker,
                            "text": " ".join(current_text),
                            "start": current_start,
                            "end": seg.get("start", 0)
                        })
                    # Начинаем новую реплику
                    current_speaker = speaker
                    current_text = [text]
                    current_start = seg.get("start", 0)
                else:
                    # Продолжаем текущую реплику
                    current_text.append(text)
            
            # Добавляем последнюю реплику
            if current_text:
                speakers_text.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text),
                    "start": current_start,
                    "end": result["segments"][-1].get("end", 0)
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
        try:
            del self.model
            del self.align_model
            if self.diarize_model:
                del self.diarize_model
            gc.collect()
        except:
            pass

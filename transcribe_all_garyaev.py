from faster_whisper import WhisperModel
import os
import glob

def run_mass_transcription():
    # Путь к аудио и куда класть транскрипты
    audio_dir = "/root/sales-ai-agent/data/audio/Garyaev_Maxim"
    out_dir = "/root/sales-ai-agent/data/transcripts/Garyaev_Maxim"
    os.makedirs(out_dir, exist_ok=True)
    
    # Загружаем модель (1.5 Гб RAM, работает быстро)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    files = glob.glob(f"{audio_dir}/*.mp3")
    print(f"Найдено файлов для обработки: {len(files)}")

    for audio_path in files:
        file_name = os.path.basename(audio_path)
        # Имя TXT будет точно таким же, как MP3 (только расширение другое)
        out_path = os.path.join(out_dir, file_name.replace(".mp3", ".txt"))
        
        if os.path.exists(out_path):
            print(f"Пропуск (уже есть): {file_name}")
            continue

        print(f"Транскрибирую: {file_name}...")
        segments, _ = model.transcribe(audio_path, beam_size=5)
        
        with open(out_path, "w", encoding="utf-8") as f:
            for segment in segments:
                f.write(f"[{segment.start:.1f}s] {segment.text.strip()}\n")
    
    print("\nГОТОВО! Все файлы в папке /data/transcripts/Garyaev_Maxim")

if __name__ == "__main__":
    run_mass_transcription()

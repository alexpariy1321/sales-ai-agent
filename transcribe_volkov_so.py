import os
import glob
from faster_whisper import WhisperModel

# 1. Настройки путей
audio_dir = "/root/sales-ai-agent/data/audio/Volkov_Full_Log"
out_dir = "/root/sales-ai-agent/data/transcripts/VolkovIvan"
os.makedirs(out_dir, exist_ok=True)

# 2. Инициализация модели Whisper (base для CPU)
print("Загрузка модели Whisper (base)...")
model = WhisperModel("base", device="cpu", compute_type="int8")

# 3. Поиск всех MP3 файлов Волкова
files = glob.glob(os.path.join(audio_dir, "*.mp3"))
print(f"Найдено файлов для транскрибации: {len(files)}")

for audio_path in sorted(files):
    filename = os.path.basename(audio_path)
    out_path = os.path.join(out_dir, filename.replace(".mp3", ".txt"))
    
    # Пропускаем, если уже транскрибировано
    if os.path.exists(out_path):
        continue
        
    print(f"Транскрибирую: {filename}...")
    try:
        segments, info = model.transcribe(audio_path, beam_size=5, language="ru")
        
        with open(out_path, "w", encoding="utf-8") as f:
            for segment in segments:
                # Формат: [00:00.0] Текст
                f.write(f"[{segment.start:.1f}s] {segment.text.strip()}\n")
                
        print(f"Готово: {out_path}")
    except Exception as e:
        print(f"Ошибка в файле {filename}: {e}")

print(f"\nВсе звонки транскрибированы в папку {out_dir}")

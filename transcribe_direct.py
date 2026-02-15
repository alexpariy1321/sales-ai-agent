from faster_whisper import WhisperModel
import os
import glob

def run_direct():
    # Ищем файл Гаряева (ivanova_elena)
    search_path = "/root/sales-ai-agent/data/audio/Garyaev_Maxim/*74912500888*2026_02_05*.mp3"
    found_files = glob.glob(search_path)
    
    if not found_files:
        print("Файл не найден!")
        return

    audio_file = found_files[0]
    print(f"--- ПРЯМАЯ ТРАНСКРИБАЦИЯ: {os.path.basename(audio_file)} ---")
    
    # Загружаем модель напрямую через faster-whisper (без Pyannote/VAD)
    # model_size "base" оптимален по скорости и качеству
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("Транскрибирую (без VAD, это надежнее)...")
    segments, info = model.transcribe(audio_file, beam_size=5)

    print(f"Определен язык: {info.language} с вероятностью {info.language_probability:.2f}")

    # Сохранение результата
    out_dir = "/root/sales-ai-agent/data/transcripts/Garyaev_Maxim"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "boss_file_direct.txt")
    
    with open(out_path, "w", encoding="utf-8") as f:
        for segment in segments:
            text = segment.text.strip()
            f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text}\n")
            print(f"[{segment.start:.1f}s] {text}")
            
    print(f"\nПОБЕДА! Полный текст сохранен в: {out_path}")

if __name__ == "__main__":
    run_direct()

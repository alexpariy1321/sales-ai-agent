import whisperx
import os
import glob

def run_local():
    search_path = "/root/sales-ai-agent/data/audio/Garyaev_Maxim/*74912500888*2026_02_05*.mp3"
    found_files = glob.glob(search_path)
    
    if not found_files:
        print("Файл не найден!")
        return

    audio_file = found_files[0]
    print(f"--- ОБРАБОТКА: {os.path.basename(audio_file)} ---")
    
    # 1. Загрузка модели
    print("Загрузка Whisper (base)...")
    model = whisperx.load_model("base", "cpu", compute_type="int8")

    # 2. Транскрибация
    print("Транскрибирую...")
    audio = whisperx.load_audio(audio_file)
    result = model.transcribe(audio, batch_size=4)

    # 3. Сохранение
    out_dir = "/root/sales-ai-agent/data/transcripts/Garyaev_Maxim"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "boss_file_local.txt")
    
    with open(out_path, "w", encoding="utf-8") as f:
        for segment in result["segments"]:
            f.write(f"{segment['text'].strip()}\n")
            
    print(f"\nПОБЕДА! Текст в: {out_path}")
    print("\n--- ФРАГМЕНТ ---")
    for segment in result["segments"][:10]:
        print(segment['text'].strip())

if __name__ == "__main__":
    run_local()

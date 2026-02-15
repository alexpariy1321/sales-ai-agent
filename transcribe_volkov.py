import os
import whisper
import json

# Конфигурация путей
BASE_PATH = "/root/sales-ai-agent/data/archive/2026-02-02_2026-02-06/SO/Volkov_Ivan"
AUDIO_DIR = os.path.join(BASE_PATH, "audio")
TRANSCRIPT_DIR = os.path.join(BASE_PATH, "transcripts")

def process():
    if not os.path.exists(TRANSCRIPT_DIR):
        os.makedirs(TRANSCRIPT_DIR)
    
    # Используем 'base' для скорости или 'turbo'/'large-v3' для качества
    print("Загрузка модели...")
    model = whisper.load_model("base")
    
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    print(f"К обработке: {len(audio_files)} файлов")
    
    for filename in audio_files:
        base_name = os.path.splitext(filename)[0]
        json_out = os.path.join(TRANSCRIPT_DIR, f"{base_name}.json")
        txt_out = os.path.join(TRANSCRIPT_DIR, f"{base_name}.txt")
        
        if os.path.exists(json_out):
            continue
            
        print(f"Транскрибируем: {filename}")
        try:
            result = model.transcribe(os.path.join(AUDIO_DIR, filename), language="ru")
            
            # Сохраняем JSON для дашборда и TXT для быстрого просмотра
            with open(json_out, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            with open(txt_out, 'w', encoding='utf-8') as f:
                f.write(result['text'])
        except Exception as e:
            print(f"Ошибка в {filename}: {e}")

if __name__ == "__main__":
    process()

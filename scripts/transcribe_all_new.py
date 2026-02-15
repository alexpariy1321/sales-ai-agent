# -*- coding: utf-8 -*-
import os
import glob
import json
from faster_whisper import WhisperModel

BASE_DIR = "/root/sales-ai-agent/data/archive"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"

def update_status(progress):
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["process_progress"] = progress
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except:
        pass

def transcribe_all():
    print("=== Запуск массовой транскрибации ===")
    update_status("Загрузка модели Whisper...")
    
    # Загружаем модель один раз (экономим время)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    # Собираем все файлы для обработки
    all_files = []
    for week in os.listdir(BASE_DIR):
        week_path = os.path.join(BASE_DIR, week)
        if not os.path.isdir(week_path):
            continue
        for company in os.listdir(week_path):
            comp_path = os.path.join(week_path, company)
            if not os.path.isdir(comp_path):
                continue
            for manager in os.listdir(comp_path):
                manager_path = os.path.join(comp_path, manager)
                audio_dir = os.path.join(manager_path, "audio")
                transcripts_dir = os.path.join(manager_path, "transcripts")
                
                if not os.path.exists(audio_dir):
                    continue
                
                # Создаём папку transcripts, если её нет
                os.makedirs(transcripts_dir, exist_ok=True)
                
                # Ищем все MP3
                mp3_files = glob.glob(os.path.join(audio_dir, "*.mp3"))
                for audio_path in mp3_files:
                    file_name = os.path.basename(audio_path)
                    txt_path = os.path.join(transcripts_dir, file_name.replace(".mp3", ".txt"))
                    
                    # Пропускаем, если уже есть
                    if os.path.exists(txt_path):
                        continue
                    
                    all_files.append({
                        "audio": audio_path,
                        "txt": txt_path,
                        "manager": manager,
                        "file_name": file_name
                    })
    
    total = len(all_files)
    if total == 0:
        print("Нет новых файлов для транскрибации.")
        update_status("Транскрибация: нет новых файлов")
        return
    
    print(f"Найдено новых файлов: {total}")
    
    # Обрабатываем каждый файл
    for i, item in enumerate(all_files, 1):
        progress = f"Транскрибация {i}/{total}: {item['manager']} - {item['file_name']}"
        print(progress)
        update_status(progress)
        
        try:
            segments, _ = model.transcribe(item["audio"], beam_size=5, language="ru")
            with open(item["txt"], "w", encoding="utf-8") as f:
                for segment in segments:
                    f.write(f"[{segment.start:.1f}s] {segment.text.strip()}\n")
            print(f"  ✓ Сохранено: {item['txt']}")
        except Exception as e:
            print(f"  ✗ Ошибка: {e}")
            # Не падаем, идём к следующему файлу
    
    print("\n=== ТРАНСКРИБАЦИЯ ЗАВЕРШЕНА ===")
    update_status(f"Транскрибация: готово ({total} файлов)")

if __name__ == "__main__":
    transcribe_all()

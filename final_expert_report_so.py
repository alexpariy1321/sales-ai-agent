import requests
import json
import os
import glob
import time

# 1. Параметры
MODEL = "qwen2.5:7b"
TRANSCRIPT_DIR = "/root/sales-ai-agent/data/transcripts/VolkovIvan"
OLLAMA_URL = "http://localhost:11434/api/generate"
FINAL_REPORT_PATH = "/root/sales-ai-agent/data/REPORT_VOLKOV_SO.md"

def ask_ollama(prompt, retries=3):
    """Отказоустойчивый запрос к Ollama с повторами"""
    for i in range(retries):
        try:
            r = requests.post(OLLAMA_URL, 
                             json={"model": MODEL, "prompt": prompt, "stream": False}, 
                             timeout=180)
            if r.status_code == 200:
                res = r.json().get("response")
                if res: return res
            time.sleep(5) # Пауза перед повтором
        except Exception:
            time.sleep(10)
    return "ОШИБКА: Модель не ответила после 3 попыток."

def process_all():
    files = sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt")))
    # Исключаем файлы-отчеты
    files = [f for f in files if "_expert" not in f and "_analysis" not in f]
    
    print(f"Запуск глубокого аудита 100 уровня. Файлов: {len(files)}")
    
    full_report = []
    full_report.append(f"# Итоговый отчет по аудиту: Иван Волков (Стандарт Ойл)\n")
    full_report.append(f"Дата анализа: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    full_report.append(f"Всего проанализировано звонков: {len(files)}\n\n")

    for idx, path in enumerate(files, 1):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        
        if len(text.strip()) < 100:
            continue # Пропускаем пустые

        fname = os.path.basename(path)
        print(f"[{idx}/{len(files)}] Анализ {fname}...")
        
        prompt = f"Проведи аудит звонка Волкова Ивана (Стандарт Ойл) по битуму. " \
                 f"Оцени по пунктам: 1. Гигиена (перебивания, паразиты). " \
                 f"2. Экспертиза (марки БНД, логистика, РВС). 3. СЛЕДУЮЩИЙ ШАГ. " \
                 f"Текст звонка: {text}"
        
        result = ask_ollama(prompt)
        
        # Формируем блок для общего отчета
        call_block = f"### Звонок №{idx}: {fname}\n\n{result}\n\n---\n"
        full_report.append(call_block)

    # Сохраняем все в ОДИН файл
    with open(FINAL_REPORT_PATH, "w", encoding="utf-8") as f:
        f.writelines(full_report)
    
    print(f"\nКЛАСС! Полный отчет сформирован: {FINAL_REPORT_PATH}")

if __name__ == "__main__":
    process_all()

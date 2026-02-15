import requests
import json
import os
import glob

# 1. Настройки
MODEL = "qwen2.5:7b"
TRANSCRIPT_DIR = "/root/sales-ai-agent/data/transcripts/VolkovIvan"
OLLAMA_URL = "http://localhost:11434/api/generate"

def expert_audit(text):
    if not text or len(text.strip()) < 100:
        return "СТАТУС: Пустой звонок / Недозвон / Слишком короткий для анализа"

    prompt = f"""
    Ты — старший аудитор РОПа Куркина. Проведи жесткий разбор звонка Ивана Волкова (Стандарт Ойл).
    
    ТЕКСТ ДИАЛОГА:
    {text}
    
    КРИТЕРИИ:
    1. Качество речи: (перебивания, паразиты).
    2. Экспертиза: (БНД 70/100, 100/130, 50/70, логистика, РВС 1500т).
    3. Дебиторка: (оплаты, долги).
    4. NEXT STEP: Четкая договоренность о дате/времени следующего контакта.
    
    ВЫДАЙ ОТЧЕТ В MARKDOWN.
    """
    
    try:
        r = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=180)
        response_json = r.json()
        content = response_json.get("response")
        return content if content else "Ошибка: Модель вернула пустой ответ"
    except Exception as e:
        return f"Ошибка при запросе к Ollama: {str(e)}"

# 2. Обработка
files = glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt"))
print(f"Запуск аудита Волкова. Файлов для анализа: {len(files)}")

for path in sorted(files):
    if "_analysis" in path or "_expert" in path: continue
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"Анализ: {os.path.basename(path)}...")
    report = expert_audit(content)
    
    # Теперь точно записываем только строку
    report_path = path.replace(".txt", "_expert.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(str(report))

print("\nАудит завершен успешно. Проверьте папку transcripts/VolkovIvan")

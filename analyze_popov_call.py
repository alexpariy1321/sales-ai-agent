import requests
import json
import os
import glob

def analyze_last():
    model = "qwen2.5:1.5b"
    # Берем последний созданный транскрипт Попова для примера
    transcript_files = glob.glob("/root/sales-ai-agent/data/transcripts/Popov_Denis/*.txt")
    if not transcript_files:
        print("Транскрипты не найдены! Сначала запусти transcribe_all_popov.py")
        return
    
    file_path = transcript_files[0]
    with open(file_path, "r", encoding="utf-8") as f:
        transcript = "".join(f.readlines()[:200]) # Берем первые 200 строк

    prompt = f"""
    ТЫ: Эксперт по обучению менеджеров продаж.
    ОБЪЕКТ АНАЛИЗА: Менеджер Денис Попов.
    
    ЗАДАЧА: Сделай аудит профессионализма для принятия решения об обучении.
    
    ОЦЕНИ ПО ФАКТАМ:
    1. УВЕРЕННОСТЬ: Есть ли в голосе (тексте) сомнения, оправдания или неуверенные интонации?
    2. ПЕРЕБИВАНИЯ: Дает ли он клиенту договорить?
    3. ИНИЦИАТИВА: Кто ведет диалог? Менеджер "ведет" клиента к цели или просто отбивается от вопросов?
    4. ОШИБКИ ПРОДАЖ: Задает ли он открытые вопросы? Выявляет ли потребность?
    5. РЕКОМЕНДАЦИЯ РОПу: Чему конкретно его нужно научить завтра, чтобы поднять конверсию?

    ТЕКСТ ЗВОНКА:
    {transcript}
    """

    print(f"--- АНАЛИЗ ПРОФЕССИОНАЛИЗМА (Файл: {os.path.basename(file_path)}) ---")
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}

    try:
        response = requests.post(url, json=payload, timeout=60)
        print("\n=== ВЕРДИКТ ДЛЯ КУРКИНА ПО ПОПОВУ ===\n")
        print(response.json().get('response', 'Нет ответа'))
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    analyze_last()

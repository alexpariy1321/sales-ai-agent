import requests
import json
import os
import glob

def analyze():
    model = "qwen2.5:1.5b"
    # Берем транскрипты Ахмедшина
    transcript_files = glob.glob("/root/sales-ai-agent/data/transcripts/Ahmedshin_Dmitry/*.txt")
    if not transcript_files:
        print("Транскрипты не найдены! Запустите сначала transcribe_all_ahmedshin.py")
        return
    
    # Анализируем первый найденный файл для теста
    file_path = transcript_files[0]
    with open(file_path, "r", encoding="utf-8") as f:
        transcript = "".join(f.readlines()[:200])

    prompt = f"""
    ЗАДАЧА: Проведи аудит звонка для РОПа. 
    МЕНЕДЖЕР: Дмитрий Ахмедшин.
    
    ОЦЕНИ ПРОФЕССИОНАЛИЗМ:
    1. ТОН И УВЕРЕННОСТЬ: Насколько убедительно звучит менеджер?
    2. УПРАВЛЕНИЕ РАЗГОВОРОМ: Кто задает вопросы, а кто отвечает? (Инициатива)
    3. СЛУШАНИЕ: Перебивает ли он клиента? Слышит ли скрытые запросы?
    4. ГЛАВНАЯ ОШИБКА: Что Дмитрий сделал не так в этом разговоре?
    5. РЕКОМЕНДАЦИЯ ПО ОБУЧЕНИЮ: Какой навык нужно прокачать Дмитрию в первую очередь?

    ТЕКСТ ЗВОНКА:
    {transcript}
    """

    print(f"--- АНАЛИЗ ЗВОНКА АХМЕДШИНА (Файл: {os.path.basename(file_path)}) ---")
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}

    try:
        response = requests.post(url, json=payload, timeout=60)
        print("\n=== ВЕРДИКТ ДЛЯ КУРКИНА ПО АХМЕДШИНУ ===\n")
        print(response.json().get('response', 'Ошибка получения ответа'))
    except Exception as e:
        print(f"Ошибка запроса: {e}")

if __name__ == "__main__":
    analyze()

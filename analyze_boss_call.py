import requests
import json
import os

def analyze():
    model = "qwen2.5:1.5b"
    # Для теста берем тот же файл
    file_path = "/root/sales-ai-agent/data/transcripts/Garyaev_Maxim/ivanova_elena_aleksandrovna_out_74912500888_2026_02_05-10_29_59_cbeg.txt"
    
    with open(file_path, "r", encoding="utf-8") as f:
        transcript = "".join(f.readlines())

    prompt = f"""
    ТЫ: Руководитель отдела продаж (РОП). Твоя цель - найти ошибки в работе менеджера.
    МЕНЕДЖЕР: Максим Гаряев (в системе ivanova_elena).
    
    ПРОАНАЛИЗИРУЙ:
    1. УВЕРЕННОСТЬ: Менеджер говорит четко или "мямлит", извиняется, сомневается?
    2. ИНИЦИАТИВА: Кто ведет разговор? Менеджер предлагает решение или просто отвечает на вопросы клиента?
    3. ОШИБКИ: Перебивает ли он? Есть ли в речи слова-паразиты?
    4. ОЦЕНКА (1-10): Насколько профессионально отработан звонок?
    5. ЧЕМУ УЧИТЬ: Какую одну конкретную вещь менеджеру нужно исправить (например: "не перебивать", "закрывать на следующий шаг", "говорить тверже о цене")?

    ТЕКСТ:
    {transcript}
    """

    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}

    try:
        response = requests.post(url, json=payload, timeout=90)
        print("\n=== АУДИТ ДЛЯ КУРКИНА (ОШИБКИ И ОБУЧЕНИЕ) ===\n")
        print(response.json().get('response', 'Нет ответа'))
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    analyze()

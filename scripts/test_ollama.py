import os
import json
import requests
import argparse
from datetime import datetime

# --- НАСТРОЙКИ ---
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"  # <--- ЛЕГКАЯ МОДЕЛЬ
BATCH_SIZE = 3               # <--- МЕНЬШЕ НАГРУЗКА

BASE_DIR = "/root/sales-ai-agent"
DATA_DIR = os.path.join(BASE_DIR, "data/archive")
PROMPTS_FILE = os.path.join(BASE_DIR, "data/prompts.json")

RUS_NAMES = {
    "Volkov_Ivan": "Иван Волков",
    "Popov_Denis": "Денис Попов",
    "Ahmedshin_Dmitry": "Дмитрий Ахмедшин",
    "Garyaev_Maxim": "Максим Гаряев",
    "Ivanova_Elena": "Елена Иванова"
}

def query_ollama_stream(messages):
    """Отправка запроса с стримингом (чтобы видеть прогресс)"""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,  # <--- ВКЛЮЧАЕМ СТРИМ
        "options": {
            "temperature": 0.3,
            "num_ctx": 4096 
        }
    }
    
    full_response = ""
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600) as r:
            if r.status_code != 200:
                print(f"❌ Ошибка API: {r.status_code}")
                return None
                
            print("   🤖 Ollama думает: ", end="", flush=True)
            for line in r.iter_lines():
                if line:
                    body = json.loads(line)
                    if "message" in body and "content" in body["message"]:
                        token = body["message"]["content"]
                        print(token, end="", flush=True)
                        full_response += token
                    if body.get("done", False):
                        break
            print("\n") # Перенос строки после ответа
            return full_response
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return None

def analyze_batch(batch_texts, batch_idx, company_context):
    print(f"\n🔹 БАТЧ #{batch_idx} ({len(batch_texts)} звонков)...")
    combined_text = "\n\n".join(batch_texts)
    
    system_prompt = "Ты аналитик. Найди ошибки и успехи в диалогах."
    user_prompt = f"""Контекст: {company_context}
    
Проанализируй диалоги. Кратко выпиши:
1. ПЛЮСЫ (фразы).
2. МИНУСЫ (ошибки).

ДИАЛОГИ:
{combined_text}
"""
    return query_ollama_stream([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])

def analyze_with_ollama(week, company, manager):
    rus_name = RUS_NAMES.get(manager, manager)
    print(f"\n🚀 ТЕСТ OLLAMA (LITE): {rus_name} | Модель: {MODEL_NAME}")
    
    mgr_dir = os.path.join(DATA_DIR, week, company, manager)
    transcripts_dir = os.path.join(mgr_dir, "transcripts")
    
    if not os.path.exists(transcripts_dir):
        print("❌ Нет транскриптов")
        return

    files = sorted([f for f in os.listdir(transcripts_dir) if f.endswith(".txt")])
    if not files: return

    # Загружаем ВСЕ
    all_calls = []
    for f in files:
        with open(os.path.join(transcripts_dir, f), "r", encoding="utf-8") as file:
            content = file.read().strip()
            if len(content) > 100:
                all_calls.append(f"=== {f} ===\n{content}")
    
    print(f"📊 Загружено {len(all_calls)} звонков.")
    
    # Разбиваем на пачки
    batches = [all_calls[i:i + BATCH_SIZE] for i in range(0, len(all_calls), BATCH_SIZE)]
    print(f"🔄 Всего {len(batches)} пачек (по {BATCH_SIZE} шт).")
    
    batch_results = []
    
    # Обрабатываем
    for i, batch in enumerate(batches, 1):
        res = analyze_batch(batch, i, "Продажи")
        if res:
            batch_results.append(res)
        else:
            print("⚠️ Пропуск пачки.")

    # Финальный отчет
    print(f"\n🏁 ГЕНЕРАЦИЯ ИТОГОВОГО ОТЧЕТА...")
    all_findings = "\n\n".join(batch_results)
    
    final_prompt = f"""Составь итоговый отчет по менеджеру {rus_name} на основе заметок:

{all_findings}

Структура:
# ОЦЕНКА (0-100)
# ГЛАВНЫЙ ВЫВОД
# ПЛЮСЫ
# МИНУСЫ
# СОВЕТЫ
"""
    final_report = query_ollama_stream([
        {"role": "user", "content": final_prompt}
    ])
    
    if final_report:
        report_path = os.path.join(mgr_dir, "report", f"OLLAMA_LITE_{manager}.md")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(final_report)
        print(f"\n✅ СОХРАНЕНО: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--manager", required=True)
    args = parser.parse_args()
    
    analyze_with_ollama(args.week, args.company, args.manager)

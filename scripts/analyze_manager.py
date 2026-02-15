import os
import sys
import json
import argparse
import time
from gigachat import GigaChat
from gigachat.models import Messages, MessagesRole
from dotenv import load_dotenv

load_dotenv("/root/sales-ai-agent/.env")
AUTH_DATA = os.getenv("GIGACHAT_CREDENTIALS")
MODEL_NAME = "GigaChat-Pro"
BASE_DIR = "/root/sales-ai-agent/data/archive"
PROMPTS_FILE = "/root/sales-ai-agent/data/prompts.json"

# Размер пакета (количество звонков в одном запросе Map-стадии)
# 10 звонков целиком ~ 20-30k символов. Это комфортно для модели.
BATCH_SIZE = 10 

def get_prompts():
    """Читает промпты из JSON-файла"""
    manager_prompt = "Проанализируй диалоги и составь отчет."
    if os.path.exists(PROMPTS_FILE):
        try:
            with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                p = data.get("manager_prompt", "").strip()
                if p: manager_prompt = p
        except: pass
    return manager_prompt

def analyze_batch(giga, texts, batch_idx):
    """Анализирует пачку звонков (Map этап)"""
    print(f"   ⚙️ Обработка пакета #{batch_idx} ({len(texts)} зв.)...")
    
    combined_text = ""
    for t in texts:
        combined_text += t + "\n\n"
        
    prompt = (
        "Ты — аналитик отдела продаж. Твоя задача — сделать ПРОМЕЖУТОЧНЫЙ анализ пачки звонков.\n"
        "Выдели:\n"
        "1. Основные ошибки менеджера в этих звонках.\n"
        "2. Успешные приемы.\n"
        "3. Общее настроение клиентов.\n"
        "4. Соблюдение скрипта (оценка).\n"
        "Отвечай кратко, тезисно, фактами. Не пиши вступлений."
    )
    
    messages = [
        Messages(role=MessagesRole.SYSTEM, content=prompt),
        Messages(role=MessagesRole.USER, content=f"Звонки:\n{combined_text}")
    ]
    
    try:
        res = giga.chat(payload={"messages": messages})
        return res.choices[0].message.content
    except Exception as e:
        print(f"   ❌ Ошибка пакета #{batch_idx}: {e}")
        return "Ошибка анализа пакета."

def analyze_manager(week, company, manager):
    print(f"🔍 [AI Map-Reduce] Анализ: {manager}")
    
    manager_path = os.path.join(BASE_DIR, week, company, manager)
    transcripts_dir = os.path.join(manager_path, "transcripts")
    report_dir = os.path.join(manager_path, "report")
    report_file = os.path.join(manager_path, f"WEEKLY_REPORT_{manager}.md")

    if not os.path.exists(transcripts_dir):
        print("⚠️ Нет папки транскрипций.")
        return

    # 1. Сбор всех файлов
    files = sorted([f for f in os.listdir(transcripts_dir) if f.endswith(".txt")])
    if not files:
        print("⚠️ Нет файлов.")
        return
        
    print(f"📂 Найдено {len(files)} звонков. Разбиваю на пакеты по {BATCH_SIZE}...")

    # 2. Формирование пакетов (читаем полные тексты!)
    batches = []
    current_batch = []
    
    for f in files:
        path = os.path.join(transcripts_dir, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            # Легкая чистка от мусора, но сохраняем суть
            if len(content) > 50: 
                current_batch.append(f"=== ЗВОНОК {f} ===\n{content}")
        
        if len(current_batch) >= BATCH_SIZE:
            batches.append(current_batch)
            current_batch = []
    
    if current_batch:
        batches.append(current_batch)

    print(f"📦 Получилось {len(batches)} пакетов.")

    # 3. MAP этап (Анализ пакетов)
    intermediate_results = []
    
    try:
        with GigaChat(credentials=AUTH_DATA, verify_ssl_certs=False, model=MODEL_NAME) as giga:
            
            for i, batch in enumerate(batches, 1):
                result = analyze_batch(giga, batch, i)
                intermediate_results.append(f"--- ПАКЕТ {i} ---\n{result}\n")
                # Пауза, чтобы не дудосить API (опционально)
                # time.sleep(1) 

            # 4. REDUCE этап (Финальный отчет)
            print("🔗 Сборка финального отчета (Reduce)...")
            
            all_intermediates = "\n".join(intermediate_results)
            
            final_system_prompt = get_prompts()
            final_user_prompt = (
                f"Я проанализировал звонки менеджера по частям. Вот {len(batches)} промежуточных отчетов.\n"
                f"На основе этих данных составь ПОЛНЫЙ ИТОГОВЫЙ ОТЧЕТ за неделю.\n"
                f"Обобщи ошибки, выдели системные проблемы, дай общую оценку.\n\n"
                f"ДАННЫЕ ПРОМЕЖУТОЧНЫХ АНАЛИЗОВ:\n{all_intermediates}"
            )

            messages = [
                Messages(role=MessagesRole.SYSTEM, content=final_system_prompt),
                Messages(role=MessagesRole.USER, content=final_user_prompt)
            ]
            
            final_res = giga.chat(payload={"messages": messages})
            report_content = final_res.choices[0].message.content
            
            # Сохранение
            os.makedirs(report_dir, exist_ok=True)
            with open(os.path.join(report_dir, f"REPORT_{week}.md"), "w", encoding="utf-8") as f:
                f.write(report_content)
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report_content)

            print(f"✅ Готово! Отчет сохранен.")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--manager", required=True)
    args = parser.parse_args()
    
    analyze_manager(args.week, args.company, args.manager)

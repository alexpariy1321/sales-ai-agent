# -*- coding: utf-8 -*-
import os
import sys
import json
import argparse
import re
from datetime import datetime
from dotenv import load_dotenv
from gigachat import GigaChat
from gigachat.models import Messages, MessagesRole

# --- КОНФИГУРАЦИЯ ---
BASE_DIR = "/root/sales-ai-agent"
DATA_DIR = os.path.join(BASE_DIR, "data/archive")
PROMPTS_FILE = os.path.join(BASE_DIR, "data/prompts.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_FILE)
GIGACHAT_KEY = os.getenv("GIGACHAT_CREDENTIALS")

# ЛИМИТЫ (ЭКОНОМНЫЙ РЕЖИМ)
TOTAL_CONTEXT_LIMIT = 80000

RUS_NAMES = {
    "Volkov_Ivan": "Иван Волков",
    "Popov_Denis": "Денис Попов",
    "Ahmedshin_Dmitry": "Дмитрий Ахмедшин",
    "Garyaev_Maxim": "Максим Гаряев",
    "Ivanova_Elena": "Елена Иванова",
    "Popov_Andrey": "Андрей Попов",
    "Akimova_Ekaterina": "Екатерина Акимова"
}

def load_prompts():
    if os.path.exists(PROMPTS_FILE):
        try:
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"system": "Ты эксперт по продажам и анализу звонков.", "companies": {}}

def classify_call_local(text):
    """
    Классифицирует звонок локально (Python) для экономии токенов.
    Возвращает: category (str), is_useful (bool)
    """
    text_lower = text.lower()
    length = len(text)

    # 1. Пустые / Недозвоны
    if length < 100:
        return "empty", False
    
    spam_markers = ["абонент недоступен", "оставьте сообщение", "вас не слышно", "перезвоните позже", "алло до свидания"]
    if any(m in text_lower for m in spam_markers) and length < 300:
        return "empty", False

    # 2. Взыскание (Дебиторка)
    debt_markers = ["долг", "просрочк", "оплат", "счет", "бухгалтер", "акт сверки", "платежк"]
    if any(m in text_lower for m in debt_markers):
        return "debt", True

    # 3. Внутренние (обычно короткие и специфичные, но пока по длине)
    # Если короткий диалог без продажи
    if length < 400 and "куп" not in text_lower and "цен" not in text_lower:
        return "internal", False

    # 4. Клиентские (все остальное полезное)
    return "client", True

def analyze_manager(week, company, manager):
    rus_name = RUS_NAMES.get(manager, manager.replace('_', ' '))
    print(f"\n🔍 УМНЫЙ АНАЛИЗ (v4.0): {rus_name}")

    mgr_dir = os.path.join(DATA_DIR, week, company, manager)
    transcripts_dir = os.path.join(mgr_dir, "transcripts")
    report_dir = os.path.join(mgr_dir, "report")

    if not os.path.exists(transcripts_dir):
        print("Нет транскриптов")
        return

    files = sorted([f for f in os.listdir(transcripts_dir) if f.endswith(".txt")])
    if not files:
        print("Пусто")
        return

    # --- СТАТИСТИКА ЗВОНКОВ ---
    stats = {
        "total": len(files),
        "empty": 0,     # Недозвоны
        "client": 0,    # Продажи
        "debt": 0,      # Взыскание
        "internal": 0   # Внутренние
    }

    useful_texts = [] # То, что отправим в GigaChat

    print(f"📄 Обработка {len(files)} файлов (Python-фильтр)...")
    
    for f in files:
        with open(os.path.join(transcripts_dir, f), "r", encoding="utf-8") as file:
            content = file.read()
            
        category, is_useful = classify_call_local(content)
        
        # Обновляем счетчики
        if category == "empty": stats["empty"] += 1
        elif category == "client": stats["client"] += 1
        elif category == "debt": stats["debt"] += 1
        elif category == "internal": stats["internal"] += 1

        # Собираем контекст только из полезных
        if is_useful:
            useful_texts.append(f"\n=== {f} [{category.upper()}] ===\n{content}")

    # Лимитируем контекст (если полезных слишком много)
    full_text = "\n".join(useful_texts)
    if len(full_text) > TOTAL_CONTEXT_LIMIT:
        print(f"⚠️ Текст обрезан: {len(full_text)} -> {TOTAL_CONTEXT_LIMIT}")
        full_text = full_text[:TOTAL_CONTEXT_LIMIT] + "\n[...ЛИМИТ...]"
    
    print(f"📊 Статистика: Всего {stats['total']} | Клиенты {stats['client']} | Долги {stats['debt']} | Пустые {stats['empty']}")

    # --- ГЕНЕРАЦИЯ ПРОМПТА ---
    prompts = load_prompts()
    sys_prompt = prompts.get("system", "Ты эксперт по продажам.")
    comp_prompt = prompts.get("companies", {}).get(company, {}).get("prompt", "")

    # Вставляем статистику прямо в промпт, чтобы ИИ её прокомментировал
    final_prompt = f"""Ты — наставник менеджера {rus_name}.
Твоя задача — составить ОТЧЁТ ПО ЗВОНКАМ.

СТАТИСТИКА ЗА НЕДЕЛЮ:
- Всего звонков: {stats['total']}
- Клиентские (продажи): {stats['client']}
- Взыскание долгов (дебиторка): {stats['debt']}
- Пустые/Недозвоны: {stats['empty']}
- Внутренние: {stats['internal']}

Контекст компании: {comp_prompt}

Проанализируй диалоги (ниже).
1. Если много "Взыскания" — оцени жесткость/корректность требований.
2. Если много "Пустых" — дай совет по времени звонка.
3. По "Клиентским" — оцени воронку продаж.

Составь ИТОГОВЫЙ ОТЧЁТ (Markdown):

# СТАТИСТИКА ЭФФЕКТИВНОСТИ
[Краткий комментарий по цифрам выше: как менеджер тратит время?]

# УРОВЕНЬ КОМПЕТЕНЦИЙ: [0-100]

# ОБРАТНАЯ СВЯЗЬ (КОУЧИНГ)
[Главный вывод]

# СИЛЬНЫЕ СТОРОНЫ
- [Навык]: [Пример]

# ТОЧКИ РОСТА
- [Проблема] -> [Решение]

# ПЛАН РАЗВИТИЯ
1. [Задача 1]
2. [Задача 2]

ТЕКСТЫ ЗВОНКОВ (ДЛЯ АНАЛИЗА):
{full_text if full_text else "[НЕТ ПОЛЕЗНЫХ ЗВОНКОВ ДЛЯ АНАЛИЗА]"}
"""

    # --- ЗАПРОС К GIGACHAT ---
    if not useful_texts:
        print("⏭️ Нет полезных звонков для GigaChat. Генерируем заглушку.")
        final_report = f"# Отчет по статистике\nПолезных разговоров не найдено.\nСтатистика:\n- Недозвоны: {stats['empty']}\n- Внутренние: {stats['internal']}"
    else:
        try:
            with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False, model="GigaChat-Pro") as giga:
                messages = [
                    Messages(role=MessagesRole.SYSTEM, content=sys_prompt),
                    Messages(role=MessagesRole.USER, content=final_prompt)
                ]
                response = giga.chat(payload={"messages": messages})
                final_report = response.choices[0].message.content
        except Exception as e:
            print(f"❌ Ошибка GigaChat: {e}")
            return

    # --- СОХРАНЕНИЕ ---
    os.makedirs(report_dir, exist_ok=True)
    
    # Markdown отчет
    report_md = f"# Еженедельный отчёт: {rus_name}\n**Неделя:** {week}\n\n{final_report}"
    with open(os.path.join(report_dir, f"WEEKLY_REPORT_{manager}.md"), "w", encoding="utf-8") as f:
        f.write(report_md)

    # JSON данные (для UI)
    score = 50
    if "УРОВЕНЬ КОМПЕТЕНЦИЙ:" in final_report:
        try: score = int(re.sub(r'\D', '', final_report.split("УРОВЕНЬ КОМПЕТЕНЦИЙ:")[1].split("\n")[0]))
        except: pass

    json_data = {
        "score": score,
        "summary": final_report[:300] + "...",
        "stats": stats,  # Сохраняем статистику в JSON для фронтенда (на будущее)
        "timestamp": datetime.now().isoformat()
    }
    
    with open(os.path.join(report_dir, f"WEEKLY_REPORT_{manager}.json"), "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False)

    print(f"✅ Отчёт готов: {report_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--manager", required=True)
    args = parser.parse_args()
    analyze_manager(args.week, args.company, args.manager)

import os
import sys
import json
import argparse
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from gigachat import GigaChat
try:
    from json_repair import repair_json
except ImportError:
    def repair_json(s): return s # Заглушка, если не установилось

# --- КОНФИГУРАЦИЯ ---
BASE_DIR = "/root/sales-ai-agent"
DATA_DIR = os.path.join(BASE_DIR, "data/archive")
PROMPTS_FILE = os.path.join(BASE_DIR, "data/prompts.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")
STATUS_FILE = os.path.join(BASE_DIR, "data/system_status.json")

load_dotenv(ENV_FILE)

RUS_NAMES = {
    "Volkov_Ivan": "Иван Волков",
    "Popov_Denis": "Денис Попов",
    "Ahmedshin_Dmitry": "Дмитрий Ахмедшин",
    "Garyaev_Maxim": "Максим Гаряев",
    "Ivanova_Elena": "Елена Иванова"
}

def analyze_manager(week, company, manager):
    rus_name = RUS_NAMES.get(manager, manager.replace('_', ' '))
    rus_name = RUS_NAMES.get(manager, manager.replace("_", " "))


GIGACHAT_KEY = os.getenv("GIGACHAT_CREDENTIALS")

def update_status(msg, is_processing=True):
    print(f"STATUS: {msg}")

def load_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def analyze_manager(week, company, manager):
    rus_name = RUS_NAMES.get(manager, manager.replace('_', ' '))
    mgr_dir = os.path.join(DATA_DIR, week, company, manager)
    transcripts_dir = os.path.join(mgr_dir, "transcripts")
    report_dir = os.path.join(mgr_dir, "report")
    
    if not os.path.exists(transcripts_dir):
        print("No transcripts found")
        return

    files = sorted([f for f in os.listdir(transcripts_dir) if f.endswith(".txt")])
    if not files:
        print("Empty transcripts folder")
        return

    print(f"Reading {len(files)} files...")
    full_text = ""
    for f in files:
        with open(os.path.join(transcripts_dir, f), "r", encoding="utf-8") as tf:
            content = tf.read()
            if len(content) > 50000: content = content[:50000] + "..."
            full_text += f"\n=== ЗВОНОК: {f} ===\n{content}\n"

    prompts = load_prompts()
    sys_prompt = prompts.get("system", "Ты строгий аудитор продаж.")
    comp_prompt = prompts.get("companies", {}).get(company, {}).get("prompt", "")
    
    # СУПЕР-ПРОМПТ 2026: Структура через Markdown, а не JSON (надежнее для LLM)
    final_prompt = f"""
{sys_prompt}

ТЫ — АУДИТОР ОТДЕЛА ПРОДАЖ. МЕНЕДЖЕР: {rus_name}
КОМПАНИЯ: {company}
КРИТЕРИИ: {comp_prompt}

ПРОАНАЛИЗИРУЙ ДИАЛОГИ И ПОДГОТОВЬ ОТЧЕТ.

СТРУКТУРА ОТВЕТА (строго следуй заголовкам):

# ОЦЕНКА: [Число 0-100]

# ОБЩИЙ ВЫВОД
[Текст вывода]

# СИЛЬНЫЕ СТОРОНЫ
- [Пункт 1 с цитатой]
- [Пункт 2 с цитатой]

# ОШИБКИ И ЗОНЫ РОСТА
- [Ошибка 1 с цитатой]
- [Ошибка 2 с цитатой]

# ЛУЧШИЙ ЗВОНОК
[Название файла]: [Почему лучший]

# ХУДШИЙ ЗВОНОК
[Название файла]: [Почему худший]

# РЕКОМЕНДАЦИИ
- [Совет 1]
- [Совет 2]

СТЕНОГРАММЫ:
{full_text[:120000]}
""" 

    print("Sending to GigaChat Pro...")
    try:
        with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False, model="GigaChat-Pro") as giga:
            response = giga.chat(final_prompt)
            answer = response.choices[0].message.content
            
            os.makedirs(report_dir, exist_ok=True)
            
            # Парсим Markdown вручную (это надежнее JSON)
            score = 50
            summary = "Не удалось извлечь вывод."
            strengths = []
            weaknesses = []
            recs = []
            best_call = "-"
            worst_call = "-"
            
            # Эвристический парсинг
            try:
                if "ОЦЕНКА:" in answer:
                    score_line = answer.split("ОЦЕНКА:")[1].split("\n")[0].strip()
                    score = int(re.sub(r'\D', '', score_line))
                
                if "# ОБЩИЙ ВЫВОД" in answer:
                    summary = answer.split("# ОБЩИЙ ВЫВОД")[1].split("#")[0].strip()
                
                # Сохраняем "сырой" ответ как MD, потому что он УЖЕ в Markdown и красивый
                final_md = f"# Отчет: {rus_name}\n**Дата:** {datetime.now().strftime('%d.%m.%Y')}\n\n{answer}"
                
                with open(os.path.join(report_dir, f"WEEKLY_REPORT_{manager}.md"), "w", encoding="utf-8") as f:
                    f.write(final_md)
                
                # Создаем JSON для карточки (только оценка и саммари)
                json_data = {
                    "score": score,
                    "summary": summary[:200] + "...",
                    "strengths": [], # В карточке не показываем, всё в отчете
                    "weaknesses": [],
                    "recommendations": [],
                    "best_call": best_call,
                    "worst_call": worst_call
                }
                
                with open(os.path.join(report_dir, f"WEEKLY_REPORT_{manager}.json"), "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                print(f"DONE: Report saved (Markdown mode).")
                
            except Exception as e:
                print(f"Error parsing MD: {e}")
                # Если парсинг упал, сохраняем как есть
                with open(os.path.join(report_dir, f"WEEKLY_REPORT_{manager}.md"), "w", encoding="utf-8") as f:
                    f.write(answer)
                with open(os.path.join(report_dir, f"WEEKLY_REPORT_{manager}.json"), "w", encoding="utf-8") as f:
                    json.dump({"score": 0, "summary": "Ошибка формата отчета"}, f)

    except Exception as e:
        print(f"Error GigaChat: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--manager", required=True)
    args = parser.parse_args()
    
    analyze_manager(args.week, args.company, args.manager)

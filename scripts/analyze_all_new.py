import os
import subprocess
import json
from datetime import datetime

BASE_DIR = "/root/sales-ai-agent/data/archive"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"
SCRIPT_PATH = "/root/sales-ai-agent/scripts/analyze_manager.py"
PYTHON_BIN = "/root/sales-ai-agent/venv/bin/python3"

def update_status(progress):
    try:
        with open(STATUS_FILE, "r") as f: data = json.load(f)
    except: data = {}
    data["process_progress"] = progress
    with open(STATUS_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False)

def main():
    if not os.path.exists(BASE_DIR):
        print("Нет данных.")
        return

    # Берем последнюю неделю
    weeks = sorted(os.listdir(BASE_DIR), reverse=True)
    if not weeks: return
    
    current_week = weeks[0] # Самая свежая неделя
    print(f"Анализируем неделю: {current_week}")

    tasks = []
    
    # Собираем список всех менеджеров
    for company in os.listdir(os.path.join(BASE_DIR, current_week)):
        comp_path = os.path.join(BASE_DIR, current_week, company)
        if not os.path.isdir(comp_path): continue
        
        for manager in os.listdir(comp_path):
            if os.path.isdir(os.path.join(comp_path, manager)):
                tasks.append((current_week, company, manager))

    total = len(tasks)
    print(f"Найдено {total} менеджеров для анализа.")

    for i, (week, comp, mgr) in enumerate(tasks, 1):
        msg = f"Анализ {i}/{total}: {mgr}"
        print(msg)
        update_status(msg)
        
        try:
            subprocess.run([
                PYTHON_BIN, SCRIPT_PATH,
                "--week", week,
                "--company", comp,
                "--manager", mgr
            ], check=True)
        except Exception as e:
            print(f"Ошибка анализа {mgr}: {e}")

    update_status("Анализ завершен")

if __name__ == "__main__":
    main()

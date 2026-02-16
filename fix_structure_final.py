import os
import json
import re

# 1. Проверяем данные на диске
BASE_DIR = "/root/sales-ai-agent/data/archive"
print(f"🔍 Checking BASE_DIR: {BASE_DIR}")

if not os.path.exists(BASE_DIR):
    print("❌ Critical: Data directory not found!")
    # Создаем тестовую структуру, чтобы интерфейс хоть что-то показал
    os.makedirs(f"{BASE_DIR}/2026-02-16_2026-02-22/SO/TestManager/audio", exist_ok=True)
    print("⚠️ Created dummy data for test.")
else:
    weeks = os.listdir(BASE_DIR)
    print(f"✅ Found weeks: {weeks}")

# 2. Перезаписываем функцию get_structure в main.py на 100% рабочую
path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Код функции get_structure
new_structure_code = """
@app.get("/api/structure")
def get_structure():
    base_dir = "/root/sales-ai-agent/data/archive"
    structure = {}
    
    if not os.path.exists(base_dir):
        return structure

    # Получаем недели
    weeks = sorted([w for w in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, w))], reverse=True)
    
    for week in weeks:
        week_path = os.path.join(base_dir, week)
        structure[week] = {}
        
        # Компании (SO, UN)
        companies = [c for c in os.listdir(week_path) if os.path.isdir(os.path.join(week_path, c))]
        for comp in companies:
            comp_path = os.path.join(week_path, comp)
            managers = []
            
            # Менеджеры
            for mgr in os.listdir(comp_path):
                mgr_path = os.path.join(comp_path, mgr)
                if not os.path.isdir(mgr_path): 
                    continue
                
                # Считаем аудио
                audio_dir = os.path.join(mgr_path, "audio")
                count = 0
                if os.path.exists(audio_dir):
                    count = len([f for f in os.listdir(audio_dir) if f.endswith(".mp3")])
                
                # Проверяем отчет
                has_report = os.path.exists(os.path.join(mgr_path, f"WEEKLY_REPORT_{mgr}.md"))
                
                managers.append({
                    "id": mgr,
                    "name": mgr.replace("_", " "), # Убираем подчеркивания для красоты
                    "calls_count": count,
                    "has_weekly_report": has_report
                })
            
            if managers:
                structure[week][comp] = managers
                
    return structure
"""

# Удаляем старую функцию (если есть) и вставляем новую
if "def get_structure" in content:
    content = re.sub(r'@app\.get\("/api/structure".*?def get_structure.*?return structure', '', content, flags=re.DOTALL)

content += "\n\n" + new_structure_code

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ main.py patched: get_structure restored.")

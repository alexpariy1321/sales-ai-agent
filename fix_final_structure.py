import os
import re

# Путь к данным, который ты подтвердил
REAL_BASE_DIR = "/root/sales-ai-agent/data/archive"

# Код новой, самой надежной функции get_structure
new_structure_code = f"""
@app.get("/api/structure")
def get_structure():
    # ЖЕЛЕЗОБЕТОННЫЙ ПУТЬ
    base_dir = "{REAL_BASE_DIR}"
    
    print(f"API: Scanning {{base_dir}}")
    structure = {{}}
    
    if not os.path.exists(base_dir):
        print(f"API Error: Base dir not found at {{base_dir}}")
        return {{}}

    # 1. Берем недели (папки, не файлы)
    try:
        weeks = sorted([w for w in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, w))], reverse=True)
    except Exception as e:
        print(f"API Error listing weeks: {{e}}")
        return {{}}

    for week in weeks:
        week_path = os.path.join(base_dir, week)
        structure[week] = {{}}
        
        # 2. Берем компании (SO, UN)
        try:
            companies = [c for c in os.listdir(week_path) if os.path.isdir(os.path.join(week_path, c))]
            
            for comp in companies:
                comp_path = os.path.join(week_path, comp)
                managers_list = []
                
                # 3. Берем менеджеров
                if not os.path.exists(comp_path): continue
                
                managers = [m for m in os.listdir(comp_path) if os.path.isdir(os.path.join(comp_path, m))]
                
                for mgr in managers:
                    mgr_path = os.path.join(comp_path, mgr)
                    
                    # Считаем аудио-файлы
                    audio_dir = os.path.join(mgr_path, "audio")
                    count = 0
                    if os.path.exists(audio_dir):
                        try:
                            count = len([f for f in os.listdir(audio_dir) if f.lower().endswith(".mp3")])
                        except: pass
                    
                    # Проверяем наличие отчета
                    # (Имя отчета может быть WEEKLY_REPORT_Ivan_Volkov.md или просто WEEKLY_REPORT.md)
                    report_exists = False
                    try:
                        files = os.listdir(mgr_path)
                        if any("WEEKLY_REPORT" in f and f.endswith(".md") for f in files):
                            report_exists = True
                    except: pass
                    
                    managers_list.append({{
                        "id": mgr,
                        "name": mgr.replace("_", " "),
                        "calls_count": count,
                        "has_weekly_report": report_exists
                    }})
                
                # Если нашли менеджеров, добавляем компанию в структуру
                if managers_list:
                    structure[week][comp] = managers_list
                    
        except Exception as e:
            print(f"API Error scanning week {{week}}: {{e}}")
            continue
            
    print(f"API: Returning structure with {{len(structure)}} weeks")
    return structure
"""

# Читаем файл main.py
path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Удаляем старую версию get_structure (любую версию)
# Используем регулярку, которая захватывает от декоратора до return structure
content = re.sub(r'@app\.get\("/api/structure".*?def get_structure.*?return structure', '', content, flags=re.DOTALL)

# Добавляем новую версию в конец
content += "\n\n" + new_structure_code

# Записываем обратно
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ main.py updated with HARDCODED path.")

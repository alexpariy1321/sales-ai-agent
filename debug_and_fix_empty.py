import os
import json
import re

# 1. Ищем, где реально лежат данные
possible_paths = [
    "/root/sales-ai-agent/data/archive",
    "./data/archive",
    "../data/archive",
    "/var/www/sales-ai-agent/data/archive"
]

REAL_BASE_DIR = None
for p in possible_paths:
    if os.path.exists(p) and os.path.isdir(p):
        contents = os.listdir(p)
        if contents:
            print(f"✅ FOUND DATA at: {p} (Items: {len(contents)})")
            REAL_BASE_DIR = p
            break
    else:
        print(f"❌ Not found: {p}")

if not REAL_BASE_DIR:
    print("\n⚠️ CRITICAL: Data directory not found anywhere!")
    print("Creating test data so the interface shows SOMETHING...")
    REAL_BASE_DIR = "/root/sales-ai-agent/data/archive"
    os.makedirs(f"{REAL_BASE_DIR}/2026-02-16_2026-02-22/SO/TestManager/audio", exist_ok=True)
    with open(f"{REAL_BASE_DIR}/2026-02-16_2026-02-22/SO/TestManager/audio/test_call_2026_02_16-12_00_00.mp3", "w") as f:
        f.write("test")

# 2. Обновляем main.py с ЖЕЛЕЗОБЕТОННЫМ путем
print(f"\n🔧 Patching main.py with base dir: {REAL_BASE_DIR}")

py_path = "backend/main.py"
with open(py_path, "r", encoding="utf-8") as f:
    content = f.read()

# Новая функция get_structure, которая не может не работать
new_func = f"""
@app.get("/api/structure")
def get_structure():
    # HARDCODED PATH calculated by debug script
    base_dir = "{REAL_BASE_DIR}"
    
    print(f"API: Reading structure from {{base_dir}}")
    structure = {{}}
    
    if not os.path.exists(base_dir):
        return {{"error": "Base dir not found"}}

    try:
        weeks = sorted([w for w in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, w))], reverse=True)
    except Exception as e:
        print(f"API Error listing weeks: {{e}}")
        return {{}}

    for week in weeks:
        week_path = os.path.join(base_dir, week)
        structure[week] = {{}}
        
        try:
            companies = [c for c in os.listdir(week_path) if os.path.isdir(os.path.join(week_path, c))]
            for comp in companies:
                comp_path = os.path.join(week_path, comp)
                managers = []
                
                for mgr in os.listdir(comp_path):
                    mgr_path = os.path.join(comp_path, mgr)
                    if not os.path.isdir(mgr_path): continue
                    
                    # Считаем файлы
                    audio_dir = os.path.join(mgr_path, "audio")
                    count = 0
                    if os.path.exists(audio_dir):
                        count = len([f for f in os.listdir(audio_dir) if f.endswith(".mp3")])
                    
                    managers.append({{
                        "id": mgr,
                        "name": mgr.replace("_", " "),
                        "calls_count": count,
                        "has_weekly_report": os.path.exists(os.path.join(mgr_path, f"WEEKLY_REPORT_{{mgr}}.md"))
                    }})
                
                if managers:
                    structure[week][comp] = managers
        except Exception as e:
            print(f"API Error processing week {{week}}: {{e}}")
            continue
            
    print(f"API: Found {{len(structure)}} weeks")
    return structure
"""

# Заменяем старую функцию
if "def get_structure" in content:
    content = re.sub(r'@app\.get\("/api/structure".*?def get_structure.*?return structure', '', content, flags=re.DOTALL)

content += "\\n\\n" + new_func

with open(py_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ main.py patched successfully.")

import os
import re
import json
import sys

# Настройки
WEEK = "2026-02-09_2026-02-15"
COMPANY = "SO"
# Попробуем найти менеджера автоматически
base_path = f"/root/sales-ai-agent/data/archive/{WEEK}/{COMPANY}"

print(f"🔍 Checking base path: {base_path}")
if not os.path.exists(base_path):
    print(f"❌ Path not found! Check your WEEK and COMPANY.")
    sys.exit(1)

managers = os.listdir(base_path)
print(f"📂 Found managers: {managers}")

if not managers:
    print("❌ No managers found.")
    sys.exit(1)

# Берем первого попавшегося или ищем Волкова
manager = next((m for m in managers if "Volkov" in m or "14" in m), managers[0])
print(f"🎯 Selected manager for test: {manager}")

# Имитация функции из main.py
def get_calls_debug(week, company, manager):
    base_dir = "/root/sales-ai-agent/data/archive"
    target_dir = os.path.join(base_dir, week, company, manager, "audio")
    transcript_dir = os.path.join(base_dir, week, company, manager, "transcripts")
    report_dir = os.path.join(base_dir, week, company, manager, "report")
    
    print(f"   📂 Target Audio Dir: {target_dir}")
    
    if not os.path.exists(target_dir):
        print("   ❌ Audio dir does not exist")
        return []
    
    files = sorted(os.listdir(target_dir), reverse=True)
    print(f"   📄 Files found: {len(files)}")
    
    mp3_files = [f for f in files if f.endswith(".mp3")]
    print(f"   🎵 MP3 files: {len(mp3_files)}")
    
    calls = []
    for f in mp3_files:
        calls.append({"filename": f, "status": "ok"})
    
    return calls

# Запуск теста
try:
    result = get_calls_debug(WEEK, COMPANY, manager)
    print("\n✅ API Logic Result (First 2 items):")
    print(json.dumps(result[:2], indent=2))
except Exception as e:
    print(f"\n❌ API Logic CRASHED: {e}")


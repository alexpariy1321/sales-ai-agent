import re

path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Старый эндпоинт
old_endpoint = """@app.get("/api/report/{week}/{company}/{manager}")
def get_report(week: str, company: str, manager: str):"""

# Новый эндпоинт с заголовками
new_endpoint = """@app.get("/api/report/{week}/{company}/{manager}")
def get_report(week: str, company: str, manager: str):
    # Пытаемся найти Markdown отчет
    report_name = f"WEEKLY_REPORT_{manager}.md"
    path = os.path.join(BASE_DIR, week, company, manager, "report", report_name)
    
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}

    if os.path.exists(path):
        return FileResponse(path, headers=headers)
    
    # Если MD нет, ищем JSON
    json_name = f"WEEKLY_REPORT_{manager}.json"
    json_path = os.path.join(BASE_DIR, week, company, manager, "report", json_name)
    if os.path.exists(json_path):
        return FileResponse(json_path, headers=headers)

    raise HTTPException(status_code=404, detail="Отчет не найден")"""

# Заменяем функцию целиком (если она не слишком изменилась, иначе лучше вручную)
# Я использую более надежный способ: просто перезапишем функцию get_report с помощью regex, если она есть
if "@app.get(\"/api/report/" in content:
    content = re.sub(r'@app\.get\("/api/report/.*?\n.*?def get_report.*?raise HTTPException.*?\n', new_endpoint + "\n", content, flags=re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Cache headers added to Report API.")
else:
    print("⚠️ Could not find report endpoint to patch.")


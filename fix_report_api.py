import re

path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Эндпоинт для отчета
new_endpoint = """
@app.get("/api/report/{week}/{company}/{manager}")
def get_report(week: str, company: str, manager: str):
    # Пытаемся найти Markdown отчет
    report_name = f"WEEKLY_REPORT_{manager}.md"
    path = os.path.join(BASE_DIR, week, company, manager, "report", report_name)
    
    if os.path.exists(path):
        return FileResponse(path)
    
    # Если MD нет, ищем JSON (на всякий случай)
    json_name = f"WEEKLY_REPORT_{manager}.json"
    json_path = os.path.join(BASE_DIR, week, company, manager, "report", json_name)
    if os.path.exists(json_path):
        return FileResponse(json_path)

    raise HTTPException(status_code=404, detail="Отчет не найден")
"""

if "/api/report/" not in content:
    content += "\n\n" + new_endpoint
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Endpoint /api/report added.")
else:
    print("⚠️ Endpoint already exists.")

import re

path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoint = """
class AnalyzeRequest(BaseModel):
    week: str
    company: str
    manager: str
    force: bool = False

@app.post("/api/analyze_manager")
def analyze_manager_endpoint(req: AnalyzeRequest):
    # Проверяем, есть ли отчет
    report_path = os.path.join(BASE_DIR, req.week, req.company, req.manager, "report", f"WEEKLY_REPORT_{req.manager}.json")
    
    if os.path.exists(report_path) and not req.force:
        return {"status": "exists", "message": "Отчет уже существует. Перезаписать?"}

    # Запускаем в отдельном потоке (но статус будем писать локально для менеджера, это сложнее, пока просто запустим)
    # Чтобы не блокировать, запускаем тред
    def run():
        update_status(f"analyzing_{req.manager}", True) # Флаг конкретного менеджера в статусе? Пока используем глобальный или просто лог
        try:
            script = os.path.join(SCRIPTS_DIR, "analyze_manager.py")
            python = "/root/sales-ai-agent/venv/bin/python3"
            subprocess.run([python, script, "--week", req.week, "--company", req.company, "--manager", req.manager], check=True)
        finally:
            update_status(f"analyzing_{req.manager}", False)

    threading.Thread(target=run).start()
    return {"status": "started", "message": "Анализ запущен"}
"""

if "/api/analyze_manager" not in content:
    content += "\n\n" + new_endpoint
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ API updated")
else:
    print("⚠️ API already exists")

import os

# ПРАВИЛЬНЫЙ ПУТЬ: просто backend/main.py, так как мы уже в корне проекта
path = "backend/main.py" 

new_endpoint = """
@app.get("/api/report/{week}/{company}/{manager}")
def get_report(week: str, company: str, manager: str):
    report_path = os.path.join(BASEDIR, week, company, manager, "report", f"WEEKLY_REPORT_{manager}.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": "Отчет еще не сформирован."}
"""

if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "def get_report" not in content:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + new_endpoint)
        print("✅ Endpoint /api/report added")
    else:
        print("⚠️ Endpoint already exists")
else:
    print(f"❌ File not found at: {path}. Current dir: {os.getcwd()}")

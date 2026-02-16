import re

path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Проверяем наличие эндпоинтов
if "/api/prompts" in content:
    print("✅ API Prompts exists.")
else:
    print("❌ API Prompts MISSING! Adding...")
    
    new_endpoints = """
@app.get("/api/prompts")
def get_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

class PromptsUpdate(BaseModel):
    system: str
    companies: dict

@app.post("/api/prompts")
def save_prompts(data: PromptsUpdate):
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, ensure_ascii=False, indent=2)
    return {"status": "saved"}
"""
    content += "\n\n" + new_endpoints
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ API Prompts added.")


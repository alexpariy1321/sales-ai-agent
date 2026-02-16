import re

path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Новый эндпоинт
new_endpoint = """
@app.get("/api/transcript/{week}/{company}/{manager}/{filename}")
def get_transcript(week: str, company: str, manager: str, filename: str):
    # Имя файла может прийти как mp3, так и txt. Нам нужен txt.
    txt_filename = filename.replace(".mp3", ".txt")
    
    path = os.path.join(BASE_DIR, week, company, manager, "transcripts", txt_filename)
    
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {"content": f.read()}
        except Exception as e:
            return {"content": f"Error reading file: {str(e)}"}
            
    return {"content": "Транскрипция не найдена."}
"""

# Вставляем перед последним эндпоинтом или в конец
if "/api/transcript/" not in content:
    content += "\n\n" + new_endpoint
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Endpoint /api/transcript added.")
else:
    print("⚠️ Endpoint already exists.")

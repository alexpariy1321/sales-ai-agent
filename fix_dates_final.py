import os
import re

path = "backend/main.py"

# Новая функция get_calls с правильным REGEX
new_code = """
@app.get("/api/calls/{week}/{company}/{manager}")
def get_calls(week: str, company: str, manager: str):
    try:
        base = "/root/sales-ai-agent/data/archive"
        target_dir = os.path.join(base, week, company, manager, "audio")
        transcript_dir = os.path.join(base, week, company, manager, "transcripts")
        report_dir = os.path.join(base, week, company, manager, "report")

        if not os.path.exists(target_dir):
            return []

        # Получаем список mp3
        files = sorted([f for f in os.listdir(target_dir) if f.endswith(".mp3")], reverse=True)
        
        # Регулярка под формат: ..._YYYY_MM_DD-HH_MM_SS_...
        # Ищем 4 цифры (год), потом _ или -, потом 2 цифры (месяц) и т.д.
        # Пример: 2026_02_16-07_51_30
        date_pattern = re.compile(r"(\d{4})[_.-](\d{2})[_.-](\d{2})[-_](\d{2})[_.-](\d{2})")

        calls = []
        for f in files:
            # Парсим дату
            match = date_pattern.search(f)
            if match:
                y, m, d, h, mn = match.groups()
                date_str = f"{d}.{m}.{y}"
                time_str = f"{h}:{mn}"
                # Сортировка: YYYYMMDDHHMM
                sort_key = f"{y}{m}{d}{h}{mn}"
            else:
                date_str = "Unknown"
                time_str = "00:00"
                sort_key = "0"

            calls.append({
                "filename": f,
                "date": date_str,
                "time": time_str,
                "sortkey": sort_key,
                "has_transcript": os.path.exists(os.path.join(transcript_dir, f.replace(".mp3", ".txt"))),
                "has_report": os.path.exists(os.path.join(report_dir, f.replace(".mp3", ".md")))
            })
            
        return calls
    except Exception as e:
        print(f"Error in get_calls: {e}")
        return []
"""

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Удаляем старую функцию get_calls
content = re.sub(r'@app\.get\("/api/calls/.*?def get_calls.*?return calls', '', content, flags=re.DOTALL)
# Если удаление не сработало (другой формат отступов), добавляем в конец (Python переопределит)
content += "\n\n" + new_code

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("✅ Dates parsing fixed in main.py")

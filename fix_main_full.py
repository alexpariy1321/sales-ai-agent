import os
import re

# Читаем текущий файл
path = "backend/main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Исправляем BASEDIR на абсолютный путь
# Ищем строку BASEDIR = ...
content = re.sub(
    r'BASEDIR\s*=\s*.*', 
    'BASEDIR = "/root/sales-ai-agent/data/archive"', 
    content
)

# 2. Обновляем get_calls на "пуленепробиваемую" версию
new_get_calls = """
@app.get("/api/calls/{week}/{company}/{manager}")
def get_calls(week: str, company: str, manager: str):
    # Строим пути
    target_dir = os.path.join(BASEDIR, week, company, manager, "audio")
    transcript_dir = os.path.join(BASEDIR, week, company, manager, "transcripts")
    report_dir = os.path.join(BASEDIR, week, company, manager, "report")
    
    calls = []
    
    # Если папки нет - возвращаем пустой список, но не ошибку
    if not os.path.exists(target_dir):
        print(f"Directory not found: {target_dir}")
        return calls

    # Регулярка для дат (поддерживает и дефисы и подчеркивания)
    # Пример: 2026-02-13-14-45-32 или 2026_02_13_14_45_32
    date_pattern = re.compile(r"(\d{4})[-_](\d{2})[-_](\d{2})[-_](\d{2})[-_](\d{2})[-_](\d{2})")

    try:
        files = sorted(os.listdir(target_dir), reverse=True)
    except Exception as e:
        print(f"Error listing directory: {e}")
        return []

    for f in files:
        if not f.endswith(".mp3"):
            continue

        # Проверяем наличие транскрипции
        txt_name = f.replace(".mp3", ".txt")
        has_transcript = os.path.exists(os.path.join(transcript_dir, txt_name))
        
        # Проверяем наличие отчета
        report_name = f.replace(".mp3", ".md")
        has_report = os.path.exists(os.path.join(report_dir, report_name))

        # Парсим дату
        match = date_pattern.search(f)
        if match:
            y, m, d, h, mn, s = match.groups()
            date_str = f"{d}.{m}.{y}"
            time_str = f"{h}:{mn}"
            sort_key = f"{y}{m}{d}{h}{mn}{s}"
        else:
            # Если дата не парсится, просто выводим имя файла
            date_str = "Unknown"
            time_str = "00:00"
            sort_key = f"000000000000_{f}" # Чтобы сортировка была хоть какой-то

        calls.append({
            "filename": f,
            "date": date_str,
            "time": time_str,
            "sortkey": sort_key,
            "has_transcript": has_transcript,  # Важно: underscore
            "has_report": has_report           # Важно: underscore
        })
    
    return calls
"""

# Удаляем старую функцию get_calls, если она есть
# Мы ищем от @app.get("/api/calls... до следующего декоратора @app или конца файла
pattern_del = r'@app\.get\("/api/calls/\{week\}/\{company\}/\{manager\}"\)(.|\n)*?(?=@app|$)'
content = re.sub(pattern_del, "", content, flags=re.MULTILINE)

# Добавляем новую версию в конец файла
content += "\n\n" + new_get_calls

# Записываем обратно
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ backend/main.py successfully patched!")

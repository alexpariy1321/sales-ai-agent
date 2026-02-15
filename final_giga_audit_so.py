import os
import glob
import time
from gigachat import GigaChat

# 1. Загрузка ключа
config = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v.strip("'\" \n")

CREDENTIALS = config.get("GIGACHAT_CREDENTIALS")
TRANSCRIPT_DIR = "/root/sales-ai-agent/data/transcripts/VolkovIvan"
REPORT_PATH = "/root/sales-ai-agent/data/EXPERT_GIGA_REPORT_VOLKOV.md"

def analyze_call(giga, text):
    prompt = f"Проведи экспертный аудит звонка Ивана Волкова (Стандарт Ойл). Текст: {text[:5000]}"
    try:
        res = giga.chat(prompt)
        return res.choices[0].message.content
    except Exception as e:
        return f"Ошибка запроса: {e}"

# 2. Запуск процесса
files = sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt")))
files = [f for f in files if "_analysis" not in f and "_expert" not in f]

print(f"Запуск GigaChat Pro. Найдено файлов: {len(files)}")

report = ["# ИТОГОВЫЙ АУДИТ GIGACHAT PRO: ИВАН ВОЛКОВ\n\n"]

# Важно: verify_ssl_certs=False помогает избежать проблем с сертификатами Минцифры
with GigaChat(credentials=CREDENTIALS, verify_ssl_certs=False, scope="GIGACHAT_API_PERS") as giga:
    for idx, path in enumerate(files, 1):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if len(content.strip()) < 150: continue

        print(f"[{idx}/{len(files)}] Анализ {os.path.basename(path)}...")
        analysis = analyze_call(giga, content)
        report.append(f"## Звонок: {os.path.basename(path)}\n\n{analysis}\n\n---\n")
        time.sleep(1)

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.writelines(report)

print(f"\nУСПЕХ! Отчет создан: {REPORT_PATH}")

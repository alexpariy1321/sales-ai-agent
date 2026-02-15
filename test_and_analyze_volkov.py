import requests
import os
import glob
import time

# 1. Настройки (Gemini API через прокси, как в документации)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
# Ключ берем из .env
config = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v.strip("'").strip('"')

API_KEY = config.get("GEMINI_API_KEY")
TRANSCRIPT_DIR = "/root/sales-ai-agent/data/transcripts/VolkovIvan"
FINAL_REPORT = "/root/sales-ai-agent/data/FINAL_EXPERT_REPORT_SO.md"

def analyze_with_gemini(text, is_test=False):
    """Запрос к Gemini 1.5 Flash"""
    prompt = f"Проведи аудит звонка менеджера Волкова (Стандарт Ойл) по битуму. Тест: {is_test}. Текст: {text[:2000]}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        r = requests.post(f"{GEMINI_URL}?key={API_KEY}", json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"Ошибка API: {r.status_code}"
    except Exception as e:
        return f"Ошибка сети: {e}"

# --- ШАГ 1: ТЕСТ МОДЕЛИ ---
print("--- ТЕСТИРОВАНИЕ МОДЕЛИ ---")
test_res = analyze_with_gemini("Привет, это тестовый запрос. Ответь одним словом OK.", is_test=True)
if "OK" not in test_res.upper() and "Ошибка" in test_res:
    print(f"ТЕСТ ПРОВАЛЕН: {test_res}. Проверьте GEMINI_API_KEY.")
    exit()
print("ТЕСТ ПРОЙДЕН. Модель активна.\n")

# --- ШАГ 2: МАССОВЫЙ АНАЛИЗ ---
files = sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt")))
print(f"Начинаю экспертный аудит {len(files)} файлов...")

report_content = [f"# ЭКСПЕРТНЫЙ АУДИТ SO: ИВАН ВОЛКОВ\nGenerated: {time.ctime()}\n\n"]

for idx, path in enumerate(files, 1):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    
    if len(text.strip()) < 150: continue

    print(f"[{idx}/{len(files)}] Обработка {os.path.basename(path)}...")
    analysis = analyze_with_gemini(text)
    
    report_content.append(f"## Анализ звонка: {os.path.basename(path)}\n\n{analysis}\n\n---\n")
    time.sleep(2) # Лимиты бесплатного API

# --- ШАГ 3: СОХРАНЕНИЕ ---
with open(FINAL_REPORT, "w", encoding="utf-8") as f:
    f.writelines(report_content)

print(f"\nВСЁ! Полный экспертный отчет готов: {FINAL_REPORT}")

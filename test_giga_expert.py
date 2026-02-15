import os
import glob
from gigachat import GigaChat

# 1. Читаем .env
config = {}
with open(".env") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            config[k] = v.strip("'\" \n")

CRED = config.get("GIGACHAT_CREDENTIALS")

# 2. Берем ОДИН файл для теста
files = sorted(glob.glob("/root/sales-ai-agent/data/transcripts/VolkovIvan/*.txt"))
if not files:
    print("Файлы не найдены!")
    exit()

test_file = files[0]
with open(test_file, "r", encoding="utf-8") as f:
    text = f.read()

print(f"ТЕСТ: Анализируем звонок {os.path.basename(test_file)}...")

# 3. Запрос к GigaChat Pro
with GigaChat(credentials=CRED, verify_ssl_certs=False, scope="GIGACHAT_API_PERS") as giga:
    prompt = f"""
    Ты — ведущий аудитор нефтехимической отрасли. Проанализируй этот звонок Ивана Волкова.
    ИСПОЛЬЗУЙ СКРИПТ: РВС 1500т, БНД 70/100, 100/130, дебиторка, зимний завоз.
    
    ОТЧЕТ ДОЛЖЕН БЫТЬ ЖЕСТКИМ И ПОДРОБНЫМ:
    - Оценка навыков (1-10)
    - Соблюдение скрипта (проценты)
    - Выявленные ошибки в терминологии
    - Рекомендация РОПу
    
    ТЕКСТ: {text[:5000]}
    """
    
    try:
        res = giga.chat(prompt)
        content = res.choices[0].message.content
        print("\n--- РЕЗУЛЬТАТ ТЕСТА ---")
        print(content)
        print("-----------------------\n")
        
        with open("test_analysis_result.md", "w", encoding="utf-8") as out:
            out.write(content)
        print("Результат также сохранен в test_analysis_result.md")
    except Exception as e:
        print(f"ОШИБКА МОДЕЛИ: {e}")

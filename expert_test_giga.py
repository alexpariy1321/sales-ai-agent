import os
import glob
from gigachat import GigaChat

# 1. Загрузка ключа
config = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v.strip("'\" \n")

CRED = config.get("GIGACHAT_CREDENTIALS")

# 2. Выбор файла
files = sorted(glob.glob("/root/sales-ai-agent/data/transcripts/VolkovIvan/*.txt"))
if not files:
    print("Ошибка: Транскрипты не найдены!")
    exit()

test_file = files[0]
with open(test_file, "r", encoding="utf-8") as f:
    text = f.read()

print(f"--- ТЕСТ С МОДЕЛЬЮ PRO: {os.path.basename(test_file)} ---")

# 3. Явное указание модели GigaChat-Pro
with GigaChat(credentials=CRED, verify_ssl_certs=False, scope="GIGACHAT_API_PERS") as giga:
    # Добавили параметр model="GigaChat-Pro"
    payload = {
        "model": "GigaChat-Pro",
        "messages": [
            {"role": "system", "content": "Ты эксперт по битуму. Проанализируй звонок Ивана Волкова."},
            {"role": "user", "content": text[:5000]}
        ]
    }
    
    try:
        # Используем прямой вызов для большей стабильности
        res = giga.chat(payload)
        print("\nУСПЕХ! ОТВЕТ:")
        print(res.choices[0].message.content)
    except Exception as e:
        print(f"ОШИБКА: {e}")
        print("\nСОВЕТ: Если ошибка 402 сохраняется, подождите еще 5 минут. Сбер обновляет баланс API не мгновенно.")

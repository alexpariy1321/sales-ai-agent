import requests
import os
import time

# 1. Настройки
config = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v.strip("'").strip('"')

webhook = config.get("SO_BITRIX_WEBHOOK_BASE")
# Создаем отдельную папку для Ивана
base_path = "/root/sales-ai-agent/data/audio/VolkovIvan_Original"
os.makedirs(base_path, exist_ok=True)

# 2. Запрос (фильтр админа из Нерудной)
url = f"{webhook}voximplant.statistic.get.json"
params = {
    "FILTER[>=CALL_START_DATE]": "2026-02-02T00:00:00",
    "FILTER[<=CALL_START_DATE]": "2026-02-06T23:59:59",
    "FILTER[!CALL_RECORD_URL]": "null",
    "SORT": "CALL_START_DATE",
    "ORDER": "ASC"
}

print("Скачивание оригинальных файлов Ивана Волкова (SO)...")
try:
    response = requests.get(url, params=params, timeout=30).json()
    calls = response.get("result", [])
    
    count = 0
    for c in calls:
        file_url = c.get('CALL_RECORD_URL', '')
        if 'volkov_ivan' in file_url.lower():
            # СОХРАНЯЕМ ОРИГИНАЛЬНОЕ НАЗВАНИЕ
            original_name = file_url.split('/')[-1]
            filepath = os.path.join(base_path, original_name)
            
            print(f"Загрузка: {original_name}")
            audio_res = requests.get(file_url, timeout=60)
            if audio_res.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(audio_res.content)
                count += 1
            time.sleep(0.1)

    print(f"\nУспех! В папку {base_path} сохранено {count} оригинальных файлов.")

except Exception as e:
    print(f"Ошибка: {e}")

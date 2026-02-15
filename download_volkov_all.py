import requests
import os
import time

# 1. Загрузка конфига
config = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v.strip("'").strip('"')

webhook = config.get("SO_BITRIX_WEBHOOK_BASE")
base_path = "/root/sales-ai-agent/data/audio/Volkov_Full_Log"
os.makedirs(base_path, exist_ok=True)

# 2. Получаем ВСЕ звонки за период
url = f"{webhook}voximplant.statistic.get.json"
params = {
    "FILTER[>=CALL_START_DATE]": "2026-02-02T00:00:00",
    "FILTER[<=CALL_START_DATE]": "2026-02-06T23:59:59",
    "FILTER[!CALL_RECORD_URL]": "null",
    "LIMIT": 500
}

print("Анализируем звонки для поиска ID Ивана Волкова...")
try:
    response = requests.get(url, params=params, timeout=30).json()
    all_calls = response.get("result", [])
    
    # Сначала найдем PORTAL_USER_ID Ивана по его фамилии в URL
    volkov_id = None
    for c in all_calls:
        if 'volkov_ivan' in c.get('CALL_RECORD_URL', '').lower():
            volkov_id = c.get('PORTAL_USER_ID')
            break
            
    if not volkov_id:
        print("Не удалось автоматически определить ID Волкова. Проверьте имя в Битрикс.")
        exit()
        
    print(f"Определен ID Ивана Волкова: {volkov_id}. Начинаю скачивание...")

    downloaded = 0
    for c in all_calls:
        # Условие: Либо ID совпадает, либо имя в URL (на всякий случай)
        if c.get('PORTAL_USER_ID') == volkov_id or 'volkov_ivan' in c.get('CALL_RECORD_URL', '').lower():
            file_url = c.get('CALL_RECORD_URL')
            original_name = file_url.split('/')[-1]
            filepath = os.path.join(base_path, original_name)
            
            call_type = "Входящий" if c.get('CALL_TYPE') == '1' else "Исходящий"
            print(f"[{call_type}] Скачиваю: {original_name}")
            
            res = requests.get(file_url, timeout=60)
            if res.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(res.content)
                downloaded += 1
            time.sleep(0.1)

    print(f"\nГотово! Скачано {downloaded} звонков (входящих и исходящих).")

except Exception as e:
    print(f"Ошибка: {e}")

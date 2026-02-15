import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("/root/sales-ai-agent/.env")
WEBHOOK = os.getenv("SO_BITRIX_WEBHOOK_BASE")
URL = f"{WEBHOOK}voximplant.statistic.get.json"

# Для SO нужен POST и ID=11
payload = {
    "FILTER[>=CALL_START_DATE]": "2026-02-10T00:00:00",
    "FILTER[<=CALL_START_DATE]": "2026-02-12T23:59:59",
    "FILTER[PORTAL_USER_ID]": 11,
    "LIMIT": 5
}

print(f"Запрос к {URL} (POST)...")
r = requests.post(URL, json=payload)
print(f"Status: {r.status_code}")
try:
    data = r.json()
    calls = data.get("result", [])
    print(f"Найдено звонков Волкова: {len(calls)}")
    if calls:
        print("Пример звонка:")
        print(json.dumps(calls[0], indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Ошибка JSON: {e}")
    print(r.text)

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("/root/sales-ai-agent/.env")

# Настройки
UN_WEBHOOK = os.getenv("UN_BITRIX_WEBHOOK_BASE")
SO_WEBHOOK = os.getenv("SO_BITRIX_WEBHOOK_BASE")

# Период: 09.02 - 12.02 (включительно)
DATE_START = "2026-02-09T00:00:00"
DATE_END = "2026-02-12T23:59:59"

def check_company(name, webhook, is_post=False):
    if not webhook:
        print(f"{name}: Нет вебхука")
        return

    url = f"{webhook}voximplant.statistic.get.json"
    
    # Фильтр: Только с записью разговора!
    params = {
        "FILTER[>=CALL_START_DATE]": DATE_START,
        "FILTER[<=CALL_START_DATE]": DATE_END,
        "FILTER[!CALL_RECORD_URL]": "null",  # Самое важное!
        "SELECT[]": "ID" # Нам нужно только количество
    }
    
    try:
        if is_post:
            # Для SO (Волков)
            params["FILTER[PORTAL_USER_ID]"] = 11
            r = requests.post(url, json=params, timeout=30)
        else:
            # Для UN
            r = requests.get(url, params=params, timeout=30)
            
        data = r.json()
        calls = data.get("result", [])
        total = len(calls)
        
        # Если 50 (лимит), значит их может быть больше
        suffix = "+" if total == 50 else ""
        
        print(f"📊 {name}: Найдено {total}{suffix} записей разговоров.")
        
        if total == 0:
            # Проверим БЕЗ фильтра записи, чтобы понять, были ли вообще звонки
            del params["FILTER[!CALL_RECORD_URL]"]
            if is_post: r = requests.post(url, json=params)
            else: r = requests.get(url, params=params)
            all_calls = len(r.json().get("result", []))
            print(f"   (Всего звонков, включая недозвоны/гудки: {all_calls})")
            
    except Exception as e:
        print(f"❌ Ошибка {name}: {e}")

print(f"🔍 Проверка наличия ЗАПИСЕЙ (MP3) с {DATE_START} по {DATE_END}...\n")
check_company("UN (Юнион)", UN_WEBHOOK)
check_company("SO (Волков)", SO_WEBHOOK, is_post=True)

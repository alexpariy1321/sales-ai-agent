import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Загружаем конфиг
BASE_DIR = "/root/sales-ai-agent"
ENV_FILE = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_FILE)

UN_WEBHOOK = os.getenv("UN_BITRIX_WEBHOOK_BASE")
SO_WEBHOOK = os.getenv("SO_BITRIX_WEBHOOK_BASE")

# Дата сегодня
today = datetime.now().strftime("%Y-%m-%d")
print(f"\n📅 ПРОВЕРКА ЗВОНКОВ ЗА {today} (В БИТРИКСЕ)\n")

def check_company(name, webhook):
    if not webhook:
        print(f"❌ Нет вебхука для {name}")
        return

    method = "voximplant.statistic.get.json"
    url = f"{webhook}{method}"
    
    # Фильтр: звонки за сегодня
    params = {
        "FILTER[>=CALL_START_DATE]": f"{today}T00:00:00",
        "FILTER[<=CALL_START_DATE]": f"{today}T23:59:59"
    }
    
    # Для SO добавляем ID Волкова, как в основном скрипте
    if name == "SO":
        params["FILTER[PORTAL_USER_ID]"] = 14

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if "error" in data:
            print(f"⚠️ Ошибка API {name}: {data['error_description']}")
            return

        calls = data.get("result", [])
        print(f"--- {name}: Найдено {len(calls)} звонков ---")
        
        for c in calls:
            has_rec = "✅ ЗАПИСЬ ЕСТЬ" if c.get('CALL_RECORD_URL') else "❌ БЕЗ ЗАПИСИ"
            duration = c.get('CALL_DURATION', 0)
            
            # Показываем детали
            print(f"📞 ID: {c.get('ID')} | {c.get('CALL_START_DATE')} | {duration} сек | {has_rec}")
            
            # Проверяем, почему может не качаться
            if int(duration) < 5:
                print(f"   ⚠️ Короткий звонок (<5 сек), скрипт его игнорирует?")
            if not c.get('CALL_RECORD_URL'):
                print(f"   ⚠️ Нет URL записи")
                
        print("-" * 40 + "\n")

    except Exception as e:
        print(f"❌ Ошибка соединения с {name}: {e}")

# Проверяем обе компании
check_company("UN (Union)", UN_WEBHOOK)
check_company("SO (Standard Oil)", SO_WEBHOOK)

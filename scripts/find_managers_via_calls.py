# -*- coding: utf-8 -*-
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем .env
load_dotenv("/root/sales-ai-agent/.env")

# Словари компаний
COMPANIES = {
    "UN": os.getenv("UN_BITRIX_WEBHOOK_BASE"),
    "SO": os.getenv("SO_BITRIX_WEBHOOK_BASE")
}

def get_call_managers(name, hook):
    if not hook:
        print(f"⚠️  {name}: Нет вебхука в .env")
        return

    print(f"\n🔍 Ищем менеджеров в {name} (через ЗВОНКИ за неделю)...")
    
    # 1. Запрос звонков (voximplant.statistic.get)
    try:
        # Берем звонки с понедельника
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        url = f"{hook}voximplant.statistic.get"
        response = requests.post(url, json={
            "FILTER": {">CALL_START_DATE": start_date},
            "SORT": "CALL_START_DATE",
            "ORDER": "DESC"
        })
        
        calls = response.json().get("result", [])
        
        if not calls:
            print(f"⚠️  Звонков за неделю не найдено (или нет прав).")
            return

        print(f"✅ Найдено {len(calls)} звонков.")
        
        # 2. Собираем ID менеджеров (PORTAL_USER_ID)
        managers = {} # ID -> {COUNT, LAST_CALL}
        
        for call in calls:
            uid = call.get("PORTAL_USER_ID")
            if not uid: continue
            
            if uid not in managers:
                managers[uid] = {"count": 0, "last": call.get("CALL_START_DATE")}
            
            managers[uid]["count"] += 1
        
        # 3. Вывод таблицы
        print(f"{'ID':<6} | {'ЗВОНКОВ':<8} | {'ПОСЛЕДНИЙ':<20} | {'ИМЯ (Пробуем user.get)'}")
        print("-" * 65)
        
        for uid, stats in managers.items():
            # Пробуем узнать имя (может не сработать)
            name_str = "[Нет доступа]"
            try:
                res = requests.post(f"{hook}user.get", json={"ID": uid}, timeout=2).json()
                if "result" in res and res["result"]:
                    u = res["result"][0]
                    name_str = f"{u.get('LAST_NAME','')} {u.get('NAME','')}".strip()
            except:
                pass
            
            print(f"{uid:<6} | {stats['count']:<8} | {stats['last']:<20} | {name_str}")

    except Exception as e:
        print(f"❌ Ошибка {name}: {e}")

# Запуск
for n, h in COMPANIES.items():
    get_call_managers(n, h)

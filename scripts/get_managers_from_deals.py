# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv

load_dotenv("/root/sales-ai-agent/.env")

COMPANIES = {
    "UN": os.getenv("UN_BITRIX_WEBHOOK_BASE"),
    "SO": os.getenv("SO_BITRIX_WEBHOOK_BASE")
}

def get_managers_from_deals(name, hook):
    print(f"\n🔍 Ищем менеджеров в {name} (через сделки)...")
    
    # 1. Берем последние 50 сделок
    try:
        url_deals = f"{hook}crm.deal.list"
        response = requests.post(url_deals, json={
            "order": {"DATE_CREATE": "DESC"},
            "select": ["ID", "TITLE", "ASSIGNED_BY_ID"],
            "filter": {">DATE_CREATE": "2026-01-01"} # Свежие
        })
        deals = response.json().get("result", [])
        
        if not deals:
            print(f"⚠️  Сделок не найдено (или нет прав crm.deal.list).")
            return

        # Собираем уникальные ID
        manager_ids = set()
        for d in deals:
            manager_ids.add(d.get("ASSIGNED_BY_ID"))
        
        print(f"✅ Найдено {len(manager_ids)} уникальных ID менеджеров: {manager_ids}")
        
        # 2. Теперь по каждому ID узнаем Имя (user.get с ID)
        print(f"{'ID':<6} | {'ИМЯ'}")
        print("-" * 30)
        
        for mid in manager_ids:
            try:
                # user.get по конкретному ID обычно РАЗРЕШЕН, даже если список закрыт
                res_user = requests.post(f"{hook}user.get", json={"ID": mid})
                users = res_user.json().get("result", [])
                if users:
                    u = users[0]
                    full_name = f"{u.get('LAST_NAME','')} {u.get('NAME','')}".strip()
                    print(f"{mid:<6} | {full_name}")
                else:
                    print(f"{mid:<6} | [Нет доступа к имени]")
            except:
                print(f"{mid:<6} | [Ошибка запроса]")

    except Exception as e:
        print(f"❌ Ошибка {name}: {e}")

for n, h in COMPANIES.items():
    if h: get_managers_from_deals(n, h)

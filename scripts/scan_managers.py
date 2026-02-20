# -*- coding: utf-8 -*-
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем настройки
load_dotenv("/root/sales-ai-agent/.env")

COMPANIES = {
    "UN (Union)": os.getenv("UN_BITRIX_WEBHOOK_BASE"),
    "SO (Standard Oil)": os.getenv("SO_BITRIX_WEBHOOK_BASE")
}

def scan_managers(company_name, webhook):
    if not webhook:
        print(f"⚠️  {company_name}: Нет вебхука.")
        return

    print(f"\n🔍 Сканируем {company_name} (ищем ID менеджеров)...")

    # Берем звонки за 14 дней (чтобы точно всех найти)
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    url = f"{webhook}voximplant.statistic.get"
    
    try:
        # Запрашиваем звонки
        response = requests.post(url, json={
            "FILTER": {">CALL_START_DATE": start_date},
            "SELECT": ["ID", "PORTAL_USER_ID", "PORTAL_NUMBER", "PHONE_NUMBER"],
            "SORT": "CALL_START_DATE",
            "ORDER": "DESC"
        })
        calls = response.json().get("result", [])
        
        if not calls:
            print(f"❌ Звонков не найдено (или нет прав).")
            return

        # Группируем по ID
        managers = {} # ID -> {count, phones, name}
        
        for call in calls:
            uid = call.get("PORTAL_USER_ID")
            if not uid: continue
            
            # Номер телефона (портальный)
            p_num = call.get("PORTAL_NUMBER", "")
            
            if uid not in managers:
                managers[uid] = {"count": 0, "phones": set(), "name": "?"}
            
            managers[uid]["count"] += 1
            if p_num: managers[uid]["phones"].add(p_num)

        # Пробуем узнать имена (user.get по ID)
        print(f"{'ID':<6} | {'ИМЯ (из CRM)':<20} | {'ТЕЛЕФОН (из звонков)':<20} | {'КОЛ-ВО'}")
        print("-" * 65)

        for uid, data in managers.items():
            # Запрос имени
            try:
                u_res = requests.post(f"{webhook}user.get", json={"ID": uid}).json()
                if "result" in u_res and u_res["result"]:
                    u = u_res["result"][0]
                    data["name"] = f"{u.get('LAST_NAME','')} {u.get('NAME','')}".strip()
                else:
                    data["name"] = "[Нет доступа]"
            except:
                data["name"] = "[Ошибка API]"

            phones_str = ", ".join(list(data["phones"])[:2]) # Берем пару номеров
            print(f"{uid:<6} | {data['name']:<20} | {phones_str:<20} | {data['count']}")

    except Exception as e:
        print(f"❌ Ошибка {company_name}: {e}")

# Запуск
for name, hook in COMPANIES.items():
    scan_managers(name, hook)

# -*- coding: utf-8 -*-
import os
import json
import requests
from dotenv import load_dotenv

# Загружаем настройки из .env
load_dotenv("/root/sales-ai-agent/.env")

# Словари компаний
COMPANIES = {
    "UN (Union)": os.getenv("UN_BITRIX_WEBHOOK_BASE"),
    "SO (Standard Oil)": os.getenv("SO_BITRIX_WEBHOOK_BASE")
}

def get_managers(company_name, webhook):
    if not webhook:
        print(f"⚠️  Пропускаем {company_name}: вебхук не найден в .env")
        return

    print(f"\n📡 === {company_name} === (Запрос users...)")
    try:
        url = f"{webhook}user.get"
        # Фильтр: только активные
        response = requests.post(url, json={"FILTER": {"ACTIVE": "true"}})
        response.raise_for_status()
        data = response.json()

        if "result" not in data:
            print(f"❌ Битрикс {company_name} не вернул список.")
            return

        users = data["result"]
        print(f"✅ Найдено активных сотрудников: {len(users)}")

        # Заголовок таблицы
        print(f"{'ID':<4} | {'ИМЯ ФАМИЛИЯ':<22} | {'РАБ. ТЕЛ.':<12} | {'МОБИЛЬНЫЙ':<12} | {'ВНУТР.'}")
        print("-" * 65)

        # Целевые фамилии (для подсветки)
        targets_rus = ["волков", "попов", "ахмедшин", "гаряев", "иванова", "андрей"]
        
        for u in users:
            uid = u.get('ID', '-')
            name = u.get('NAME', '')
            last = u.get('LAST_NAME', '')
            full_name = f"{last} {name}".strip()
            
            # Телефоны (бывает список или строка)
            work = u.get('WORK_PHONE', '-')
            mobile = u.get('PERSONAL_MOBILE', '-')
            inner = u.get('UF_PHONE_INNER', '-') # Кастомное поле часто

            # Подсветка наших
            marker = " "
            for t in targets_rus:
                if t in full_name.lower():
                    marker = "⭐"
                    break
            
            print(f"{uid:<4} | {marker} {full_name:<20} | {work:<12} | {mobile:<12} | {inner}")

    except Exception as e:
        print(f"❌ Ошибка {company_name}: {e}")

# Запуск по очереди
for name, hook in COMPANIES.items():
    get_managers(name, hook)

print("\n🏁 Готово.")

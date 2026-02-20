import os
import json
import requests
from dotenv import load_dotenv

# Загружаем настройки
load_dotenv("/root/sales-ai-agent/.env")
webhook = os.getenv("BITRIX_WEBHOOK")

if not webhook:
    print("❌ ОШИБКА: BITRIX_WEBHOOK не найден в .env")
    exit(1)

# Исправляем URL если надо
if not webhook.endswith('/'):
    webhook += '/'

print(f"📡 Запрос списка сотрудников через: {webhook}user.get ...")

try:
    # Запрашиваем ВСЕХ активных пользователей
    response = requests.post(
        f"{webhook}user.get", 
        json={"FILTER": {"ACTIVE": "true"}}
    )
    response.raise_for_status()
    data = response.json()
    
    if "result" not in data:
        print("❌ Битрикс не вернул список пользователей.")
        print(data)
        exit(1)

    users = data["result"]
    print(f"\n✅ Найдено активных сотрудников: {len(users)}\n")

    # Красивая табличка
    header = f"{'ID':<5} | {'ИМЯ ФАМИЛИЯ':<25} | {'РАБ. ТЕЛЕФОН':<15} | {'МОБИЛЬНЫЙ':<15} | {'ВНУТР.'}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    # Список тех, кого мы ищем (для подсветки)
    targets = ["Volkov", "Popov", "Ahmedshin", "Garyaev", "Ivanova"]

    for u in users:
        uid = u.get('ID', '-')
        name = u.get('NAME', '')
        last = u.get('LAST_NAME', '')
        full_name = f"{last} {name}".strip()
        
        work_phone = u.get('WORK_PHONE', '-')
        mobile = u.get('PERSONAL_MOBILE', '-')
        inner = u.get('UF_PHONE_INNER', '-') # Внутренний номер часто тут

        # Маркер, если это наш менеджер
        marker = " "
        for t in targets:
            if t.lower() in full_name.lower(): # Простая проверка по фамилии транслитом или рус
                marker = "⭐" # Звездочка для наших
                break
        
        # Если фамилия на русском, тоже подсветим (у нас маппинг в коде RUS_NAMES)
        target_rus = ["Волков", "Попов", "Ахмедшин", "Гаряев", "Иванова"]
        for t in target_rus:
            if t.lower() in full_name.lower():
                marker = "⭐"

        print(f"{uid:<5} | {marker} {full_name:<23} | {work_phone:<15} | {mobile:<15} | {inner}")

    print("-" * len(header))
    print("⭐ - Вероятно, это целевые менеджеры (из твоего списка)")

except Exception as e:
    print(f"\n❌ Ошибка при запросе: {e}")


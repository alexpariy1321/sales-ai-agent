# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv

load_dotenv("/root/sales-ai-agent/.env")

# Словари компаний
COMPANIES = {
    "UN (Union)": os.getenv("UN_BITRIX_WEBHOOK_BASE"),
    "SO (Standard Oil)": os.getenv("SO_BITRIX_WEBHOOK_BASE")
}

def check_webhook(name, url):
    if not url:
        print(f"⚠️  {name}: URL не найден в .env")
        return

    # Убираем user.get, пробуем profile (самый безобидный метод)
    # Или app.info (информация о приложении)
    test_url = f"{url}app.info" 
    
    print(f"📡 Проверка {name} ({test_url})...")
    
    try:
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                print(f"✅ {name}: Вебхук ЖИВОЙ! (Версия API: {data['result'].get('VERSION', '?')})")
            else:
                print(f"❓ {name}: Ответ странный: {data}")
        elif response.status_code == 401:
            print(f"❌ {name}: 401 Unauthorized (Токен неверный или истек срок/права)")
        elif response.status_code == 403:
            print(f"⛔ {name}: 403 Forbidden (Нет прав на app.info, но вебхук существует)")
        else:
            print(f"⚠️  {name}: Ошибка {response.status_code}")

    except Exception as e:
        print(f"❌ Ошибка соединения {name}: {e}")

print("--- ПРОВЕРКА ДОСТУПА К БИТРИКС ---")
for name, url in COMPANIES.items():
    check_webhook(name, url)
print("----------------------------------")

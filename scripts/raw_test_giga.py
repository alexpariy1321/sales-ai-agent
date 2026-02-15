import os
import requests
import json
import uuid
from dotenv import load_dotenv

# Загружаем .env
load_dotenv("/root/sales-ai-agent/.env")
AUTH_DATA = os.getenv("GIGACHAT_CREDENTIALS")

if not AUTH_DATA:
    print("❌ Нет ключа в .env")
    exit(1)

print(f"🔑 Использую ключ: {AUTH_DATA[:10]}...")

# 1. Получаем токен доступа (Bearer Token)
url_auth = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
headers_auth = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'RqUID': str(uuid.uuid4()),
    'Authorization': f'Basic {AUTH_DATA}'
}

try:
    print("⏳ Получаю токен (v2/oauth)...")
    res = requests.post(url_auth, headers=headers_auth, data={'scope': 'GIGACHAT_API_PERS'}, verify=False)
    
    if res.status_code != 200:
        print(f"❌ Ошибка получения токена: {res.status_code}")
        print(res.text)
        exit(1)
        
    access_token = res.json()['access_token']
    print("✅ Токен получен!")
    
except Exception as e:
    print(f"❌ Ошибка соединения (Auth): {e}")
    exit(1)

# 2. Делаем запрос к модели
url_chat = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
headers_chat = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {access_token}',
    'X-Client-ID': str(uuid.uuid4()) # Для статистики
}

payload = {
    "model": "GigaChat", # Или GigaChat:latest
    "messages": [
        {"role": "user", "content": "Скажи: Система работает!"}
    ],
    "temperature": 0.7
}

try:
    print("⏳ Отправляю промпт...")
    res = requests.post(url_chat, headers=headers_chat, json=payload, verify=False)
    
    if res.status_code == 200:
        print(f"🤖 ОТВЕТ: {res.json()['choices'][0]['message']['content']}")
    else:
        print(f"❌ Ошибка чата: {res.status_code}")
        print(res.text)

except Exception as e:
    print(f"❌ Ошибка соединения (Chat): {e}")

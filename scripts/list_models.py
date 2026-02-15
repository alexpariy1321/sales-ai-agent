import os
import requests
import uuid
import json
from dotenv import load_dotenv

# 1. Авторизация (копируем из прошлого скрипта, т.к. она работает)
load_dotenv("/root/sales-ai-agent/.env")
AUTH = os.getenv("GIGACHAT_CREDENTIALS")

print("⏳ Получаю токен...")
res = requests.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    headers={'RqUID': str(uuid.uuid4()), 'Authorization': f'Basic {AUTH}'},
    data={'scope': 'GIGACHAT_API_PERS'},
    verify=False
)

if res.status_code != 200:
    print(f"Ошибка Auth: {res.text}")
    exit(1)

token = res.json()['access_token']

# 2. Запрашиваем СПИСОК МОДЕЛЕЙ
print("⏳ Запрашиваю список моделей...")
res = requests.get(
    "https://gigachat.devices.sberbank.ru/api/v1/models",
    headers={'Authorization': f'Bearer {token}'},
    verify=False
)

if res.status_code == 200:
    models = res.json()['data']
    print("\n✅ ДОСТУПНЫЕ МОДЕЛИ:")
    for m in models:
        print(f"- {m['id']}")
else:
    print(f"Ошибка Models: {res.status_code} {res.text}")

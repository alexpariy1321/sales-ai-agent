import requests
import os

def load_config():
    config = {}
    with open('/root/sales-ai-agent/.env') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                config[k] = v.strip('"').strip("'")
    return config

conf = load_config()
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={conf['GEMINI_API_KEY']}"
proxies = {"http": conf['PROXY_URL'], "https": conf['PROXY_URL']}

print("--- ЗАПРОС СПИСКА МОДЕЛЕЙ ---")
res = requests.get(url, proxies=proxies)
if res.status_code == 200:
    models = res.json().get('models', [])
    for m in models:
        if 'flash' in m['name'].lower():
            print(f"Доступная модель: {m['name']} (Методы: {m['supportedGenerationMethods']})")
else:
    print(f"Ошибка {res.status_code}: {res.text}")

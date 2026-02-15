import os
from gigachat import GigaChat
from dotenv import load_dotenv

load_dotenv("/root/sales-ai-agent/.env")
AUTH = os.getenv("GIGACHAT_CREDENTIALS")
MODEL = "GigaChat-Pro"  # <-- Проверяем конкретно эту модель

print(f"⏳ Тест модели {MODEL}...")

try:
    with GigaChat(credentials=AUTH, verify_ssl_certs=False, model=MODEL) as giga:
        res = giga.chat("Напиши одно слово: 'Работает!'")
        print(f"🤖 Ответ: {res.choices[0].message.content}")
        print("✅ Модель доступна и отвечает.")

except Exception as e:
    print(f"❌ Ошибка модели {MODEL}: {e}")

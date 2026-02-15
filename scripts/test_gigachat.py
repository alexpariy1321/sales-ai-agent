import os
from gigachat import GigaChat
from dotenv import load_dotenv

# 1. Загружаем переменные из .env
load_dotenv("/root/sales-ai-agent/.env")
GIGACHAT_KEY = os.getenv("GIGACHAT_CREDENTIALS")

if not GIGACHAT_KEY:
    print("❌ ОШИБКА: Не найден GIGACHAT_CREDENTIALS в .env")
    exit(1)

print(f"✅ Ключ найден: {GIGACHAT_KEY[:10]}...")

# 2. Инициализация (verify_ssl_certs=False, scope=GIGACHAT_API_PERS по умолчанию)
print("⏳ Отправляю запрос в GigaChat...")

try:
    with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
        # Простой чат
        response = giga.chat("Привет! Напиши одну фразу: 'Система готова к анализу!'")
        
        # Получаем ответ (content)
        answer = response.choices[0].message.content
        print(f"\n🤖 Ответ GigaChat:\n{answer}")

except Exception as e:
    print(f"\n❌ Ошибка подключения: {e}")

import os
import requests
import json

def get_env():
    env = {}
    if os.path.exists('/root/sales-ai-agent/.env'):
        with open('/root/sales-ai-agent/.env') as f:
            for line in f:
                if '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().replace('"', '').replace("'", "")
    return env

ENV = get_env()
PROXIES = {"http": ENV.get("PROXY_URL"), "https": ENV.get("PROXY_URL")}
SO_WEBHOOK = ENV.get("SO_BITRIX_WEBHOOK_BASE")

print("=== ТЕСТ GET-запроса для SO (как для UN) ===\n")

DATE_START = "2026-02-09T00:00:00"
DATE_END = "2026-02-13T23:59:59"

# GET с params (метод UN)
params = {
    "FILTER[>=CALL_START_DATE]": DATE_START,
    "FILTER[<=CALL_START_DATE]": DATE_END,
    "FILTER[!CALL_RECORD_URL]": "null",
    "start": 0
}

url = f"{SO_WEBHOOK}voximplant.statistic.get.json"

print(f"URL: {url}")
print(f"Params: {params}\n")

print("--- Запрос 1: GET + params (start=0) ---")
r1 = requests.get(url, params=params, proxies=PROXIES, timeout=60).json()

calls1 = r1.get("result", [])
total1 = r1.get("total", "нет")
next1 = r1.get("next", "нет")

print(f"✅ Получено звонков: {len(calls1)}")
print(f"   Total: {total1}")
print(f"   Next: {next1}")

if calls1:
    first_date = calls1[0].get("CALL_START_DATE", "НЕТ ДАТЫ")
    last_date = calls1[-1].get("CALL_START_DATE", "НЕТ ДАТЫ")
    print(f"   Первый звонок: ID={calls1[0].get('ID')}, Дата={first_date}")
    print(f"   Последний звонок: ID={calls1[-1].get('ID')}, Дата={last_date}")

    # Проверяем, попадают ли даты в нужный диапазон
    if "2026-02" in first_date:
        print("   ✅ ДАТА ПРАВИЛЬНАЯ (февраль 2026)!")
    else:
        print(f"   ❌ ДАТА НЕ ТА! Ожидали 09-13 февраля 2026, получили {first_date}")
else:
    print("   ❌ Звонков не найдено!")

print("\n--- Запрос 2: GET + params (start=50) ---")
params["start"] = 50
r2 = requests.get(url, params=params, proxies=PROXIES, timeout=60).json()

calls2 = r2.get("result", [])
print(f"✅ Получено звонков: {len(calls2)}")
if calls2:
    print(f"   Первый звонок: ID={calls2[0].get('ID')}, Дата={calls2[0].get('CALL_START_DATE')}")

# Проверяем дубликаты
if calls1 and calls2:
    ids1 = set(c.get("ID") for c in calls1)
    ids2 = set(c.get("ID") for c in calls2)
    overlap = ids1 & ids2
    print(f"\n📊 Дубликатов между запросами: {len(overlap)}/50")
    if len(overlap) == 0:
        print("   ✅ Pagination работает корректно!")

# Сохраняем результат
with open("/root/sales-ai-agent/test_get_method.json", "w", encoding="utf-8") as f:
    json.dump({
        "method": "GET with params",
        "total": total1,
        "first_call_date": calls1[0].get("CALL_START_DATE") if calls1 else None,
        "sample_calls": calls1[:5] if calls1 else []
    }, f, ensure_ascii=False, indent=2)

print("\n✅ Результат сохранён: /root/sales-ai-agent/test_get_method.json")

import requests
import os

# 1. Читаем .env вручную
config = {}
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                config[k] = v.strip("'").strip('"')

webhook = config.get("SO_BITRIX_WEBHOOK_BASE")
output_file = "so_calls_full_list.txt"

# 2. Формируем запрос по совету админа (через URL параметры)
# Добавляем метод voximplant.statistic.get.json
url = f"{webhook}voximplant.statistic.get.json"

# Параметры фильтрации в формате, который "любит" Битрикс
params = {
    "FILTER[>=CALL_START_DATE]": "2026-02-02T00:00:00",
    "FILTER[<=CALL_START_DATE]": "2026-02-06T23:59:59",
    "FILTER[!CALL_RECORD_URL]": "null", # Как советовал админ
    "SORT": "CALL_START_DATE",
    "ORDER": "ASC"
}

print(f"Запрос к SO через GET-параметры...")

try:
    # Используем GET вместо POST, передавая params
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    calls = data.get("result", [])
    
    if not calls:
        print("Звонки не найдены. Проверьте фильтр.")
        if "error" in data: print(f"Ошибка Битрикс: {data['error_description']}")
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"{'#':<4} | {'ID':<7} | {'Дата':<19} | {'Файл'}\n")
            f.write("-" * 90 + "\n")
            for i, c in enumerate(calls, 1):
                url_rec = c.get('CALL_RECORD_URL', '')
                fname = url_rec.split('/')[-1] if url_rec else "no_url"
                f.write(f"{i:<4} | {c.get('ID'):<7} | {c.get('CALL_START_DATE')[:19]:<19} | {fname}\n")
        
        print(f"Успех! Найдено и сохранено {len(calls)} звонков.")
        print(f"Файл: {output_file}")

except Exception as e:
    print(f"Произошла ошибка: {e}")

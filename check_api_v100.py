import requests
import os

def load_webhook():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if 'UN_BITRIX_WEBHOOK_BASE' in line:
                    return line.split('=')[1].strip().strip('"').strip("'")
    return None

def test():
    webhook = load_webhook()
    url = f"{webhook}voximplant.statistic.get.json"
    
    # Пробуем 3 разных формата даты, которые ест Bitrix
    dates_to_test = [
        ("2026-02-02", "2026-02-07"),
        ("02.02.2026", "07.02.2026"),
        ("2026-02-02T00:00:00", "2026-02-07T00:00:00")
    ]
    
    print("--- ДИАГНОСТИКА API BITRIX24 ---")
    
    for start, end in dates_to_test:
        payload = {
            "FILTER[>CALL_START_DATE]": start,
            "FILTER[<CALL_START_DATE]": end,
            "FILTER[!CALL_RECORD_URL]": "null",
            "LIMIT": 5
        }
        try:
            r = requests.post(url, data=payload, timeout=20).json()
            total = r.get('total', 0)
            print(f"Формат {start}: Найдено {total} звонков")
            if total > 0:
                # Посмотрим один звонок, чтобы увидеть его структуру
                sample = r.get('result', [{}])[0]
                print(f"Пример PORTAL_NUMBER из API: {sample.get('PORTAL_NUMBER')}")
                break
        except Exception as e:
            print(f"Ошибка с форматом {start}: {e}")

if __name__ == "__main__":
    test()

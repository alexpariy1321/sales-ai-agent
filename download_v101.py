import requests
import os

def load_webhook():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if 'UN_BITRIX_WEBHOOK_BASE' in line:
                    return line.split('=')[1].strip().strip('"').strip("'")
    return None

def run():
    webhook = load_webhook()
    if not webhook:
        print("Ошибка: Вебхук не найден")
        return

    # МАППИНГ (префикс + обязателен)
    MANAGERS = {
        'Garyaev_Maxim': '+79221610964',
        'Popov_Denis': '+79221421423',
        'Ahmedshin_Dmitry': '+79292021732'
    }
    
    date_start = '2026-02-02'
    date_end = '2026-02-07'
    base_path = '/root/sales-ai-agent/data/audio'
    
    print(f"--- ЗАПУСК СКАЧИВАНИЯ (ОРИГИНАЛЬНЫЕ ИМЕНА) ---")

    for m_name, portal in MANAGERS.items():
        print(f"\nСинхронизация: {m_name}")
        m_total = 0
        last_date = date_start
        
        while True:
            payload = {
                'FILTER[>CALL_START_DATE]': last_date,
                'FILTER[<CALL_START_DATE]': date_end,
                'FILTER[PORTAL_NUMBER]': portal,
                'FILTER[!CALL_RECORD_URL]': 'null',
                'SORT': 'CALL_START_DATE',
                'ORDER': 'ASC',
                'LIMIT': 50
            }
            
            try:
                r = requests.post(f"{webhook}voximplant.statistic.get.json", data=payload, timeout=30).json()
                calls = r.get('result', [])
                if not calls:
                    break
                
                path = os.path.join(base_path, m_name)
                os.makedirs(path, exist_ok=True)
                
                for c in calls:
                    url = c.get('CALL_RECORD_URL')
                    # Извлекаем оригинальное имя файла из URL
                    original_name = url.split('/')[-1].split('?')[0]
                    file_path = os.path.join(path, original_name)
                    
                    # Проверка типа для лога (1-In, 2-Out)
                    c_type = "Входящий" if c.get("CALL_TYPE") == "1" else "Исходящий"
                    
                    if not os.path.exists(file_path):
                        res = requests.get(url, timeout=60)
                        if res.status_code == 200:
                            with open(file_path, 'wb') as f:
                                f.write(res.content)
                            m_total += 1
                            print(f"  [{m_total}] {c_type}: {original_name}")
                    
                    last_date = c.get('CALL_START_DATE')
                
                if len(calls) < 50:
                    break
                    
            except Exception as e:
                print(f" Ошибка: {e}")
                break
        
        print(f" Завершено для {m_name}. Файлов: {m_total}")

    print(f"\n--- ВСЕ ЗВОНКИ СКАЧАНЫ В /data/audio/ ---")

if __name__ == "__main__":
    run()

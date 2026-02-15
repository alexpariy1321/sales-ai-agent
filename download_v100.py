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

    # ТОЧНЫЙ МАППИНГ (префикс + обязателен для Bitrix API)
    MANAGERS = {
        'Garyaev_Maxim': '+79221610964',
        'Popov_Denis': '+79221421423',
        'Ahmedshin_Dmitry': '+79292021732'
    }
    
    date_start = '2026-02-02'
    date_end = '2026-02-07'
    base_path = '/root/sales-ai-agent/data/audio'
    
    print(f"--- ТОЧЕЧНАЯ ВЫГРУЗКА ПО МЕНЕДЖЕРАМ (02-06 фев) ---")

    for m_name, portal in MANAGERS.items():
        print(f"\nРаботаю с менеджером: {m_name} (портал {portal})")
        m_total = 0
        last_date = date_start
        
        while True:
            # Запрашиваем звонки конкретно для этого PORTAL_NUMBER
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
                    call_id = c.get('ID')
                    file_url = c.get('CALL_RECORD_URL')
                    # Имя файла: ID_ТИП_ДАТА (1-входящий, 2-исходящий)
                    call_type = "IN" if c.get("CALL_TYPE") == "1" else "OUT"
                    file_path = os.path.join(path, f"{call_id}_{call_type}.mp3")
                    
                    if not os.path.exists(file_path):
                        res = requests.get(file_url, timeout=60)
                        if res.status_code == 200:
                            with open(file_path, 'wb') as f:
                                f.write(res.content)
                            m_total += 1
                            print(f"  [{m_total}] {call_type} сохранен: {call_id}")
                    
                    last_date = c.get('CALL_START_DATE')
                
                if len(calls) < 50:
                    break
                    
            except Exception as e:
                print(f" Ошибка для {m_name}: {e}")
                break
        
        print(f" Итого для {m_name}: {m_total} файлов")

    print(f"\n--- ВСЕ ОПЕРАЦИИ ЗАВЕРШЕНЫ ---")

if __name__ == "__main__":
    run()

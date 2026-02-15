import os
import requests
import json
import time
from urllib.parse import urlparse

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

CONFIG = {
    "UN": {
        "webhook": ENV.get("UN_BITRIX_WEBHOOK_BASE"),
        "managers": {"79221610964": "Garyaev_Maxim", "79221421423": "Popov_Denis", "79292021732": "Ahmedshin_Dmitry"}
    },
    "SO": {
        "webhook": ENV.get("SO_BITRIX_WEBHOOK_BASE"),
        "managers": {"volkov_ivan": "Volkov_Ivan"} # Ищем по строке в URL
    }
}

DATE_START = "2026-02-09T00:00:00"
DATE_END = "2026-02-13T23:59:59"
BASE_PATH = "/root/sales-ai-agent/data/archive/2026-02-09_2026-02-13"

def run():
    print(f"=== ЗАПУСК v12 (SMART SEARCH): {DATE_START[:10]} - {DATE_END[:10]} ===")
    os.makedirs(BASE_PATH, exist_ok=True)
    PROGRESS_FILE = os.path.join(BASE_PATH, "progress_state.json")
    
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f: progress = json.load(f)
        except: progress = {}

    for co_code, data in CONFIG.items():
        if not data["webhook"]: continue
        print(f"\n--- Компания {co_code} ---")
        start = progress.get(co_code, 0)
        
        while True:
            params = {
                "FILTER[>=CALL_START_DATE]": DATE_START,
                "FILTER[<=CALL_START_DATE]": DATE_END,
                "FILTER[!CALL_RECORD_URL]": "null",
                "start": start
            }

            try:
                url = f"{data['webhook']}voximplant.statistic.get.json"
                r = requests.get(url, params=params, proxies=PROXIES, timeout=60).json()
                calls = r.get("result", [])
                
                if not calls:
                    print("Записей на этой странице нет.")
                    break
                
                print(f"Страница {start//50 + 1} | Найдено в Битрикс: {len(calls)}")
                
                for c in calls:
                    rec_url = str(c.get("CALL_RECORD_URL", "")).lower()
                    p_num = str(c.get("PORTAL_NUMBER", ""))
                    p_num_clean = "".join(filter(str.isdigit, p_num))
                    
                    mgr_name = None
                    # Для UN ищем по номеру, для SO - по фамилии в ссылке
                    if co_code == "UN":
                        mgr_name = data["managers"].get(p_num_clean)
                    else:
                        if "volkov_ivan" in rec_url:
                            mgr_name = "Volkov_Ivan"

                    if mgr_name:
                        audio_dir = os.path.join(BASE_PATH, co_code, mgr_name, "audio")
                        os.makedirs(audio_dir, exist_ok=True)
                        os.makedirs(os.path.join(BASE_PATH, co_code, mgr_name, "transcripts"), exist_ok=True)
                        os.makedirs(os.path.join(BASE_PATH, co_code, mgr_name, "report"), exist_ok=True)

                        f_name = os.path.basename(urlparse(c.get("CALL_RECORD_URL")).path)
                        f_path = os.path.join(audio_dir, f_name)

                        if not os.path.exists(f_path):
                            try:
                                # Качаем без прокси
                                ra = requests.get(c.get("CALL_RECORD_URL"), timeout=90)
                                if ra.status_code == 200:
                                    with open(f_path, "wb") as f: f.write(ra.content)
                                    print(".", end="", flush=True)
                            except: print("!", end="", flush=True)

                start += 50
                progress[co_code] = start
                with open(PROGRESS_FILE, "w") as f: json.dump(progress, f)
                if len(calls) < 50: break
                
            except Exception as e:
                print(f"\n[AUTO-RETRY] Ошибка: {e}. Ждем 5 сек...")
                time.sleep(5)
                continue

    print(f"\n=== ЗАВЕРШЕНО: {BASE_PATH} ===")

if __name__ == "__main__":
    run()

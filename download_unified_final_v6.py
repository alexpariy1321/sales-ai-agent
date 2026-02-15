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
        "managers": {"11": "Volkov_Ivan"}
    }
}

# --- ПЕРИОД ТЕСТА ---
DATE_START = "2026-02-02T00:00:00"
DATE_END = "2026-02-06T23:59:59"
FOLDER_NAME = "2026-02-02_2026-02-06"
BASE_PATH = f"/root/sales-ai-agent/data/archive/{FOLDER_NAME}"

def run():
    print(f"=== ЗАПУСК (ОРИГИНАЛЬНЫЕ ИМЕНА): {FOLDER_NAME} ===")
    os.makedirs(BASE_PATH, exist_ok=True)
    PROGRESS_FILE = os.path.join(BASE_PATH, "progress_state.json")
    
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f: progress = json.load(f)

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
            if co_code == "SO":
                params["FILTER[PORTAL_USER_ID]"] = 11

            try:
                print(f"Запрос {co_code} (start={start})...", end=" ", flush=True)
                r_raw = requests.get(f"{data['webhook']}voximplant.statistic.get.json", params=params, proxies=PROXIES, timeout=60)
                r = r_raw.json()
                calls = r.get("result", [])
                print(f"Найдено: {len(calls)}")
                
                if not calls: break
                
                for c in calls:
                    p_num, p_user = str(c.get("PORTAL_NUMBER", "")), str(c.get("PORTAL_USER_ID", ""))
                    p_num_clean = "".join(filter(str.isdigit, p_num))
                    
                    mgr_name = data["managers"].get(p_num_clean) or data["managers"].get(p_user)
                    
                    if mgr_name:
                        mgr_dir = os.path.join(BASE_PATH, co_code, mgr_name)
                        audio_dir = os.path.join(mgr_dir, "audio")
                        os.makedirs(audio_dir, exist_ok=True)
                        os.makedirs(os.path.join(mgr_dir, "transcripts"), exist_ok=True)
                        os.makedirs(os.path.join(mgr_dir, "report"), exist_ok=True)

                        record_url = c.get("CALL_RECORD_URL")
                        f_name = os.path.basename(urlparse(record_url).path)
                        if not f_name: f_name = f"call_{c.get('ID')}.mp3"
                        f_path = os.path.join(audio_dir, f_name)

                        if not os.path.exists(f_path):
                            try:
                                # Скачивание без прокси
                                ra = requests.get(record_url, timeout=90)
                                if ra.status_code == 200:
                                    with open(f_path, "wb") as f: f.write(ra.content)
                                    print(".", end="", flush=True)
                            except: print("!", end="", flush=True)

                start += 50
                progress[co_code] = start
                with open(PROGRESS_FILE, "w") as f: json.dump(progress, f)
                if len(calls) < 50: break
                
            except Exception as e:
                print(f"\n[RETRY] Ошибка: {e}. Ждем 5 сек...")
                time.sleep(5)
                continue

    print(f"\n=== ЗАВЕРШЕНО: {BASE_PATH} ===")

if __name__ == "__main__":
    run()

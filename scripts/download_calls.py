import os
import requests
import json
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

# --- КОНФИГУРАЦИЯ ---
BASE_DIR = "/root/sales-ai-agent"
DATA_DIR = "/root/sales-ai-agent/data/archive"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"
ENV_FILE = "/root/sales-ai-agent/.env"

load_dotenv(ENV_FILE)

UN_WEBHOOK = os.getenv("UN_BITRIX_WEBHOOK_BASE")
SO_WEBHOOK = os.getenv("SO_BITRIX_WEBHOOK_BASE")

# ПРОКСИ ВООБЩЕ НЕ ИСПОЛЬЗУЕМ
# PROXY_URL = os.getenv("PROXY_URL") 
PROXIES = {} # Пустой словарь = прямое соединение

UN_MANAGERS = {
    "79221610964": "Garyaev_Maxim",
    "79221421423": "Popov_Denis", 
    "79292021732": "Ahmedshin_Dmitry"
}

def update_status(msg, is_syncing=True):
    print(f"STATUS: {msg}")
    data = {"issyncing": is_syncing, "syncprogress": msg}
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass

def get_current_week_dates():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    return start, start + timedelta(days=6)

def download_file(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return False
    
    try:
        # Убрали proxies=PROXIES
        r = requests.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ SAVED: {path}")
            return True
        else:
            print(f"❌ HTTP Error {r.status_code} for {url}")
    except Exception as e:
        print(f"❌ Download Error: {e}")
    return False

def process_company(code, webhook, start, end, folder):
    if not webhook: return 0
    url = f"{webhook}voximplant.statistic.get.json"
    
    params = {
        "FILTER[>=CALL_START_DATE]": start.strftime("%Y-%m-%dT00:00:00"),
        "FILTER[<=CALL_START_DATE]": end.strftime("%Y-%m-%dT23:59:59"),
        "FILTER[!=CALL_RECORD_URL]": "null"
    }
    if code == "SO": params["FILTER[PORTAL_USER_ID]"] = 14
    
    total = 0
    next_start = 0
    
    update_status(f"Запрос {code} (прямое соединение)...")
    
    while True:
        p = params.copy(); p["start"] = next_start
        try:
            # Убрали proxies=PROXIES
            r = requests.get(url, params=p, timeout=30)
            data = r.json()
            calls = data.get("result", [])
            
            if not calls: break
            
            for call in calls:
                mgr = "Unknown"
                if code == "UN":
                    num = str(call.get("PORTAL_NUMBER", "")).replace("+", "")
                    mgr = UN_MANAGERS.get(num, "Unknown_UN")
                elif code == "SO": mgr = "Volkov_Ivan"
                
                if "Unknown" in mgr: continue
                
                mgr_dir = os.path.join(DATA_DIR, folder, code, mgr)
                os.makedirs(os.path.join(mgr_dir, "audio"), exist_ok=True)
                os.makedirs(os.path.join(mgr_dir, "transcripts"), exist_ok=True)
                os.makedirs(os.path.join(mgr_dir, "report"), exist_ok=True)
                
                rec_url = call.get("CALL_RECORD_URL")
                if not rec_url: continue
                
                fname = os.path.basename(urlparse(rec_url).path)
                if not fname or len(fname) < 5:
                    dt = call.get('CALL_START_DATE', '').replace(':', '_').replace('-', '_').replace('T', '_')
                    fname = f"call_{call.get('ID')}_{dt}.mp3"
                
                target_path = os.path.join(mgr_dir, "audio", fname)
                
                if download_file(rec_url, target_path):
                    total += 1
                    update_status(f"Скачан {code}: {fname}")
            
            if "next" in data: 
                next_start = data["next"]
                time.sleep(0.5)
            else: break
            
        except Exception as e:
            print(f"Error {code}: {e}")
            break
            
    return total

def main():
    start, end = get_current_week_dates()
    folder = f"{start.strftime('%Y-%m-%d')}_{end.strftime('%Y-%m-%d')}"
    
    os.makedirs(os.path.join(DATA_DIR, folder), exist_ok=True)
    
    print(f"📂 Target Folder: {os.path.join(DATA_DIR, folder)}")
    
    c1 = process_company("UN", UN_WEBHOOK, start, end, folder)
    c2 = process_company("SO", SO_WEBHOOK, start, end, folder)
    
    msg = f"Новых: {c1 + c2}"
    update_status(msg, is_syncing=False)
    print(msg)

if __name__ == "__main__":
    main()

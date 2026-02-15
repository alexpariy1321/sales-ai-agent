# -*- coding: utf-8 -*-
import os
import requests
import json
import time
import sys
from urllib.parse import urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Отключаем буферизацию вывода
sys.stdout.reconfigure(line_buffering=True)

load_dotenv("/root/sales-ai-agent/.env")
ENV = os.environ
PROXIES = {"http": ENV.get("PROXY_URL"), "https": ENV.get("PROXY_URL")} if ENV.get("PROXY_URL") else None

CONFIG = {
    "UN": {
        "webhook": ENV.get("UN_BITRIX_WEBHOOK_BASE"),
        "managers": {
            "79221610964": "Garyaev_Maxim",
            "79221421423": "Popov_Denis",
            "79292021732": "Ahmedshin_Dmitry",
        }
    },
    "SO": {
        "webhook": ENV.get("SO_BITRIX_WEBHOOK_BASE"),
        "managers": {
            "14": "Volkov_Ivan",
            "volkov_ivan": "Volkov_Ivan"
        }
    }
}

DATA_DIR = "/root/sales-ai-agent/data/archive"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"

def update_ui_status(message):
    print(message)
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f: data = json.load(f)
        else: data = {}
        data["sync_progress"] = message
        if "ГОТОВО" in message: data["is_syncing"] = False
        with open(STATUS_FILE, "w") as f: json.dump(data, f)
    except: pass

def get_week_dates():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end

def run():
    start_dt, end_dt = get_week_dates()
    DATE_START = start_dt.strftime("%Y-%m-%dT00:00:00")
    DATE_END = end_dt.strftime("%Y-%m-%dT23:59:59")
    
    FOLDER_NAME = f"{start_dt.strftime('%Y-%m-%d')}_{end_dt.strftime('%Y-%m-%d')}"
    BASE_PATH = os.path.join(DATA_DIR, FOLDER_NAME)
    
    update_ui_status(f"Запуск: {FOLDER_NAME}")
    os.makedirs(BASE_PATH, exist_ok=True)
    
    PROGRESS_FILE = os.path.join(BASE_PATH, "progress_state.json")
    progress = {}
    
    # ИСПРАВЛЕННЫЙ БЛОК TRY
    if os.path.exists(PROGRESS_FILE):
        try: 
            with open(PROGRESS_FILE, "r") as f: 
                progress = json.load(f)
        except: 
            pass

    for co_code, data in CONFIG.items():
        if not data["webhook"]: continue
        
        update_ui_status(f"Компания {co_code}...")
        start_offset = progress.get(co_code, 0)
        
        while True:
            params = {
                "FILTER[>=CALL_START_DATE]": DATE_START,
                "FILTER[<=CALL_START_DATE]": DATE_END,
                "FILTER[!CALL_RECORD_URL]": "null",
                "start": start_offset,
            }

            try:
                url = f"{data['webhook']}voximplant.statistic.get.json"
                
                if co_code == "SO":
                    params["FILTER[PORTAL_USER_ID]"] = 14
                
                r = requests.get(url, params=params, proxies=PROXIES, timeout=60).json()
                calls = r.get("result", [])
                
                if not calls: break
                
                update_ui_status(f"{co_code}: Стр. {start_offset//50 + 1} ({len(calls)} зв.)")
                
                for c in calls:
                    rec_url = str(c.get("CALL_RECORD_URL", "")).lower()
                    p_num = str(c.get("PORTAL_NUMBER", ""))
                    p_user = str(c.get("PORTAL_USER_ID", ""))
                    
                    mgr_name = None
                    if co_code == "UN":
                        p_num_clean = "".join(filter(str.isdigit, p_num))
                        mgr_name = data["managers"].get(p_num_clean)
                    else:
                        if p_user == "14": mgr_name = "Volkov_Ivan"
                        elif "volkov_ivan" in rec_url: mgr_name = "Volkov_Ivan"
                    
                    if mgr_name:
                        mgr_dir = os.path.join(BASE_PATH, co_code, mgr_name)
                        os.makedirs(os.path.join(mgr_dir, "audio"), exist_ok=True)
                        os.makedirs(os.path.join(mgr_dir, "report"), exist_ok=True)
                        os.makedirs(os.path.join(mgr_dir, "transcripts"), exist_ok=True)
                        
                        f_name = os.path.basename(urlparse(c.get("CALL_RECORD_URL")).path)
                        if not f_name or len(f_name) < 3: f_name = f"call_{c.get('ID')}.mp3"
                        f_path = os.path.join(mgr_dir, "audio", f_name)
                        
                        if not os.path.exists(f_path):
                            try:
                                ra = requests.get(c.get("CALL_RECORD_URL"), timeout=90)
                                if ra.status_code == 200:
                                    with open(f_path, "wb") as f: f.write(ra.content)
                            except: pass
                
                start_offset += 50
                progress[co_code] = start_offset
                with open(PROGRESS_FILE, "w") as f: json.dump(progress, f)
                if len(calls) < 50: break
                    
            except Exception as e:
                time.sleep(5)
                continue

    update_ui_status("ГОТОВО")

if __name__ == "__main__":
    run()

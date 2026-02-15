# -*- coding: utf-8 -*-
import os
import re
import json
import subprocess
import threading
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from backend.managers_map import get_rus_name
except ImportError:
    def get_rus_name(name): return name.replace("_", " ")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "/root/sales-ai-agent/data/archive"
SCRIPTS_DIR = "/root/sales-ai-agent/scripts"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"
PROMPTS_FILE = "/root/sales-ai-agent/data/prompts.json"

if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "w") as f:
        json.dump({"is_syncing": False, "is_processing": False, "is_generating": False}, f)

# --- Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

class PromptsModel(BaseModel):
    manager_prompt: str
    company_prompt: str

# --- Helpers ---
def update_status(key, value):
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f: data = json.load(f)
        else: data = {}
        data[key] = value
        with open(STATUS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)
    except: pass

# --- Background Tasks ---
def run_sync_task():
    update_status("is_syncing", True)
    try:
        subprocess.run(["/root/sales-ai-agent/venv/bin/python3", os.path.join(SCRIPTS_DIR, "download_calls.py")], check=True)
    except Exception as e:
        update_status("last_error", str(e))
    finally:
        update_status("is_syncing", False)
        update_status("sync_progress", "Завершено")

def run_transcribe_task():
    update_status("is_processing", True)
    update_status("process_progress", "Транскрибация...")
    try:
        subprocess.run(["/root/sales-ai-agent/venv/bin/python3", os.path.join(SCRIPTS_DIR, "transcribe_all_new.py")], check=True)
        update_status("process_progress", "Транскрибация: готово")
    except Exception as e:
        update_status("last_error", str(e))
    finally:
        update_status("is_processing", False)

def run_analyze_task():
    update_status("is_processing", True)
    update_status("process_progress", "Анализ (GigaChat)...")
    try:
        subprocess.run(["/root/sales-ai-agent/venv/bin/python3", os.path.join(SCRIPTS_DIR, "analyze_all_new.py")], check=True)
        update_status("process_progress", "Анализ: готово")
    except Exception as e:
        update_status("last_error", str(e))
    finally:
        update_status("is_processing", False)

def run_report_task(week):
    update_status("is_generating", True)
    try:
        subprocess.run(["/root/sales-ai-agent/venv/bin/python3", os.path.join(SCRIPTS_DIR, "generate_weekly_report.py")], check=True)
    except Exception as e:
        update_status("last_error", str(e))
    finally:
        update_status("is_generating", False)

# --- API Endpoints ---

@app.post("/api/login")
def login(req: LoginRequest):
    if req.username == "admin" and req.password == "admin": return {"token": "fake"}
    raise HTTPException(status_code=401)

@app.get("/api/status")
def get_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f: return json.load(f)
    return {}

@app.post("/api/sync")
def start_sync():
    threading.Thread(target=run_sync_task).start()
    return {"status": "ok", "message": "Синхронизация..."}

@app.post("/api/transcribe")
def start_transcribe():
    threading.Thread(target=run_transcribe_task).start()
    return {"status": "ok", "message": "Транскрибация..."}

@app.post("/api/analyze")
def start_analyze():
    threading.Thread(target=run_analyze_task).start()
    return {"status": "ok", "message": "Анализ..."}

@app.post("/api/generate_report")
def start_report():
    threading.Thread(target=run_report_task, args=("all",)).start()
    return {"status": "ok", "message": "Отчет..."}

# --- Prompts API ---
@app.get("/api/prompts")
def get_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"manager_prompt": "", "company_prompt": ""}

@app.post("/api/prompts")
def save_prompts(prompts: PromptsModel):
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts.dict(), f, ensure_ascii=False, indent=2)
    return {"status": "ok", "message": "Промпты сохранены"}

# --- Data API ---
@app.get("/api/structure")
def get_structure():
    structure = {}
    if not os.path.exists(BASE_DIR): return structure
    weeks = sorted(os.listdir(BASE_DIR))
    for week in weeks:
        week_path = os.path.join(BASE_DIR, week)
        if not os.path.isdir(week_path): continue
        structure[week] = {}
        for company in os.listdir(week_path):
            comp_path = os.path.join(week_path, company)
            if not os.path.isdir(comp_path): continue
            managers = []
            for m in os.listdir(comp_path):
                m_path = os.path.join(comp_path, m)
                if os.path.isdir(m_path):
                    audio_count = len([f for f in os.listdir(os.path.join(m_path, "audio")) if f.endswith('.mp3')]) if os.path.exists(os.path.join(m_path, "audio")) else 0
                    report_exists = os.path.exists(os.path.join(m_path, f"WEEKLY_REPORT_{m}.md"))
                    managers.append({
                        "id": m,
                        "name": get_rus_name(m),
                        "calls_count": audio_count,
                        "has_weekly_report": report_exists
                    })
            structure[week][company] = managers
    return structure

@app.get("/api/calls/{week}/{company}/{manager}")
def get_calls(week: str, company: str, manager: str):
    target_dir = os.path.join(BASE_DIR, week, company, manager, "audio")
    transcript_dir = os.path.join(BASE_DIR, week, company, manager, "transcripts")
    report_dir = os.path.join(BASE_DIR, week, company, manager, "report")
    
    if not os.path.exists(target_dir): return []

    calls = []
    date_pattern = re.compile(r"(\d{4})_(\d{2})_(\d{2})[-_](\d{2})_(\d{2})_(\d{2})")
    
    files = sorted(os.listdir(target_dir), reverse=True)
    for f in files:
        if not f.endswith('.mp3'): continue
        
        txt_name = f.replace('.mp3', '.txt')
        has_transcript = os.path.exists(os.path.join(transcript_dir, txt_name))
        has_report = os.path.exists(os.path.join(report_dir, f"{f}.md")) or os.path.exists(os.path.join(report_dir, f.replace('.mp3', '.md')))
        
        match = date_pattern.search(f)
        if match:
            y, m, d, h, min_, sec = match.groups()
            date_str = f"{d}.{m}.{y}"
            time_str = f"{h}:{min_}"
            sort_key = f"{y}{m}{d}{h}{min_}{sec}"
        else:
            date_str = "Неизвестно"
            time_str = "--:--"
            sort_key = "000000000000"

        calls.append({
            "filename": f,
            "date": date_str,
            "time": time_str,
            "sort_key": sort_key,
            "has_transcript": has_transcript,
            "has_report": has_report
        })
    return calls

@app.get("/api/transcript/{week}/{company}/{manager}/{filename}")
def get_transcript(week: str, company: str, manager: str, filename: str):
    txt_filename = filename.replace('.mp3', '.txt')
    txt_path = os.path.join(BASE_DIR, week, company, manager, "transcripts", txt_filename)
    if not os.path.exists(txt_path):
        return {"content": "Транскрипция еще не готова."}
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        return {"content": f"Ошибка чтения: {str(e)}"}

# Отдача аудио (статикой, но через API для удобства)
@app.get("/api/audio/{week}/{company}/{manager}/{filename}")
def get_audio(week: str, company: str, manager: str, filename: str):
    file_path = os.path.join(BASE_DIR, week, company, manager, "audio", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404)


@app.get("/api/report/{week}/{company}/{manager}")
def get_manager_report(week: str, company: str, manager: str):
    report_path = os.path.join(BASE_DIR, week, company, manager, f"WEEKLY_REPORT_{manager}.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return FileResponse(report_path) # Или просто вернуть текст
    # Попробуем вернуть просто текст, чтобы фронт не качал файл, а читал
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Report not found")



@app.get("/api/calls/{week}/{company}/{manager}/report")
def get_manager_report_old_route(week: str, company: str, manager: str):
    # Пытаемся найти отчет
    report_path = os.path.join(BASE_DIR, week, company, manager, f"WEEKLY_REPORT_{manager}.md")
    
    if os.path.exists(report_path):
        # Возвращаем файл как текст, чтобы браузер открыл его
        # media_type="text/plain" заставит браузер показать его, а не скачивать
        return FileResponse(report_path, media_type="text/plain; charset=utf-8")
    
    raise HTTPException(status_code=404, detail="Отчет не найден (файл отсутствует)")



class AnalyzeRequest(BaseModel):
    week: str
    company: str
    manager: str

@app.post("/api/analyze_manager")
def analyze_single_manager(req: AnalyzeRequest):
    # Запускаем в отдельном потоке, чтобы не блокировать API
    def task():
        try:
            subprocess.run([
                "/root/sales-ai-agent/venv/bin/python3", 
                os.path.join(SCRIPTS_DIR, "analyze_manager.py"),
                "--week", req.week,
                "--company", req.company,
                "--manager", req.manager
            ], check=True)
        except Exception as e:
            print(f"Error analyzing {req.manager}: {e}")

    threading.Thread(target=task).start()
    return {"status": "ok", "message": f"Анализ менеджера {req.manager} запущен"}


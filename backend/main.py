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
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# --- КОНФИГУРАЦИЯ ---
BASE_DIR = "/root/sales-ai-agent/data/archive"
SCRIPTS_DIR = "/root/sales-ai-agent/scripts"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"
PROMPTS_FILE = "/root/sales-ai-agent/data/prompts.json"

app = FastAPI()

# Разрешаем CORS (чтобы фронтенд видел бэкенд)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- МОДЕЛИ ---
class LoginRequest(BaseModel):
    username: str
    password: str

class PromptModel(BaseModel):
    manager_prompt: str = ""
    company_prompt: str = ""

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def update_status(key, value):
    """Обновляет статус в JSON файле"""
    data = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
    
    data[key] = value
    
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except: pass

def get_rus_name(name):
    """Преобразует английское имя в читаемое (заглушка)"""
    return name.replace("_", " ")

# --- ФОНОВЫЕ ЗАДАЧИ ---
def run_script(script_name, status_key):
    """Запускает Python скрипт и обновляет статус"""
    update_status(status_key, True)
    try:
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        # Используем текущий venv
        python_exec = "/root/sales-ai-agent/venv/bin/python3"
        subprocess.run([python_exec, script_path], check=False)
    except Exception as e:
        update_status("lasterror", str(e))
    finally:
        update_status(status_key, False)

# --- API ENDPOINTS ---

@app.get("/api/status")
def get_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

@app.post("/api/sync")
def start_sync():
    threading.Thread(target=run_script, args=("download_calls.py", "issyncing")).start()
    return {"status": "started"}

@app.post("/api/transcribe")
def start_transcribe():
    threading.Thread(target=run_script, args=("transcribe_all_new.py", "isprocessing")).start()
    return {"status": "started"}

@app.post("/api/analyze")
def start_analyze():
    # Заглушка для анализа, если скрипт еще не готов
    return {"status": "started", "message": "Analysis started"}

@app.get("/api/structure")
def get_structure():
    """Возвращает структуру папок: Недели -> Компании -> Менеджеры"""
    print(f"Scanning: {BASE_DIR}")
    structure = {}
    
    if not os.path.exists(BASE_DIR):
        return {}

    try:
        # Сортируем недели (новые сверху)
        weeks = sorted([w for w in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, w))], reverse=True)
    except:
        return {}

    for week in weeks:
        week_path = os.path.join(BASE_DIR, week)
        structure[week] = {}
        
        try:
            companies = [c for c in os.listdir(week_path) if os.path.isdir(os.path.join(week_path, c))]
            for comp in companies:
                comp_path = os.path.join(week_path, comp)
                managers_list = []
                
                if not os.path.exists(comp_path): continue
                
                managers = [m for m in os.listdir(comp_path) if os.path.isdir(os.path.join(comp_path, m))]
                
                for mgr in managers:
                    mgr_path = os.path.join(comp_path, mgr)
                    
                    # Считаем mp3
                    count = 0
                    audio_dir = os.path.join(mgr_path, "audio")
                    if os.path.exists(audio_dir):
                        try:
                            count = len([f for f in os.listdir(audio_dir) if f.lower().endswith(".mp3")])
                        except: pass
                    
                    # Проверяем отчет
                    has_report = False
                    try:
                        files = os.listdir(mgr_path)
                        if any("WEEKLY_REPORT" in f for f in files):
                            has_report = True
                    except: pass
                    
                    managers_list.append({
                        "id": mgr,
                        "name": get_rus_name(mgr),
                        "calls_count": count,
                        "has_weekly_report": has_report
                    })
                
                if managers_list:
                    structure[week][comp] = managers_list
        except:
            continue
            
    return structure

@app.get("/api/calls/{week}/{company}/{manager}")
def get_calls(week: str, company: str, manager: str):
    """Возвращает список звонков для менеджера"""
    target_dir = os.path.join(BASE_DIR, week, company, manager, "audio")
    transcript_dir = os.path.join(BASE_DIR, week, company, manager, "transcripts")
    report_dir = os.path.join(BASE_DIR, week, company, manager, "report")
    
    calls = []
    if not os.path.exists(target_dir):
        return []

    try:
        files = sorted([f for f in os.listdir(target_dir) if f.endswith(".mp3")], reverse=True)
        # Регулярка: YYYY_MM_DD-HH_MM_SS
        date_pattern = re.compile(r"(\d{4})[_.-](\d{2})[_.-](\d{2})[-_](\d{2})[_.-](\d{2})")
        
        for f in files:
            # Парсинг даты
            match = date_pattern.search(f)
            if match:
                y, m, d, h, mn = match.groups()
                date_str = f"{d}.{m}.{y}"
                time_str = f"{h}:{mn}"
                sort_key = f"{y}{m}{d}{h}{mn}"
            else:
                date_str = "Unknown"
                time_str = "00:00"
                sort_key = "0"

            # Проверка наличия транскрибации и анализа
            txt_name = f.replace(".mp3", ".txt")
            has_transcript = os.path.exists(os.path.join(transcript_dir, txt_name))
            
            # (Упрощенно: считаем, что анализ есть, если есть общий отчет, или можно проверять отдельные файлы)
            has_report = False 

            calls.append({
                "filename": f,
                "date": date_str,
                "time": time_str,
                "sortkey": sort_key,
                "has_transcript": has_transcript,
                "has_report": has_report
            })
    except Exception as e:
        print(f"Error getting calls: {e}")
        return []
        
    return calls

@app.get("/api/audio/{week}/{company}/{manager}/{filename}")
def get_audio(week: str, company: str, manager: str, filename: str):
    path = os.path.join(BASE_DIR, week, company, manager, "audio", filename)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404)




@app.get("/api/transcript/{week}/{company}/{manager}/{filename}")
def get_transcript(week: str, company: str, manager: str, filename: str):
    # Имя файла может прийти как mp3, так и txt. Нам нужен txt.
    txt_filename = filename.replace(".mp3", ".txt")
    
    path = os.path.join(BASE_DIR, week, company, manager, "transcripts", txt_filename)
    
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {"content": f.read()}
        except Exception as e:
            return {"content": f"Error reading file: {str(e)}"}
            
    return {"content": "Транскрипция не найдена."}

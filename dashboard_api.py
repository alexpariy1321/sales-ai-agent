import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# Разрешаем запросы с нашего фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path("/root/sales-ai-agent/data/archive")

# Маппинг имен (как в ваших инструкциях)
MANAGERS_MAP = {
    "ivanova_elena": "Максим Гаряев",
    "Garyaev_Maxim": "Максим Гаряев",
    "dmitriy_akhmedshin": "Дмитрий Ахмедшин", 
    "Ahmedshin_Dmitry": "Дмитрий Ахмедшин",
    "popov_denis": "Денис Попов",
    "Popov_Denis": "Денис Попов",
    "shevchuk_dmitriy": "Константин Сергеев",
    "Sergeev_Konstantin": "Константин Сергеев",
    "volkov_ivan": "Иван Волков",
    "Volkov_Ivan": "Иван Волков"
}

@app.get("/api/structure")
def get_structure():
    """Сканирует папки и возвращает дерево: Неделя -> Компания -> Менеджер"""
    structure = {}
    
    if not BASE_DIR.exists():
        return {"error": "Archive folder not found"}

    # Сортируем недели (новые сверху)
    weeks = sorted([d for d in BASE_DIR.iterdir() if d.is_dir()], reverse=True)
    
    for week_dir in weeks:
        week_name = week_dir.name
        structure[week_name] = {}
        
        for company_dir in week_dir.iterdir():
            if not company_dir.is_dir(): continue
            company_name = company_dir.name
            
            managers = []
            for mgr_dir in company_dir.iterdir():
                if not mgr_dir.is_dir() or mgr_dir.name == "summary": continue
                
                # Считаем кол-во звонков
                audio_dir = mgr_dir / "audio"
                call_count = len(list(audio_dir.glob("*.mp3"))) if audio_dir.exists() else 0
                
                managers.append({
                    "id": mgr_dir.name,
                    "name": MANAGERS_MAP.get(mgr_dir.name, mgr_dir.name),
                    "calls_count": call_count
                })
            
            structure[week_name][company_name] = managers
            
    return structure

@app.get("/api/calls/{week}/{company}/{manager}")
def get_calls(week: str, company: str, manager: str):
    """Возвращает список звонков менеджера"""
    target_dir = BASE_DIR / week / company / manager
    audio_dir = target_dir / "audio"
    
    if not audio_dir.exists():
        return []
        
    calls = []
    # Сортируем файлы по дате (свежие сверху)
    files = sorted(audio_dir.glob("*.mp3"), key=os.path.getmtime, reverse=True)
    
    for f in files:
        # --- ИСПРАВЛЕНИЕ ДАТЫ ---
        try:
            # Имя файла: 2026-02-03_14-30-55_79...mp3
            # Берем первые 19 символов: "2026-02-03_14-30-55"
            date_str = f.name[:19]
            dt = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
            date_ts = dt.timestamp()
        except ValueError:
            # Если имя файла нестандартное, берем дату создания файла
            date_ts = f.stat().st_mtime
        # ------------------------

        calls.append({
            "filename": f.name,
            "url": f"/api/audio/{week}/{company}/{manager}/{f.name}",
            "date": date_ts
        })
    
    # Сортируем список по РЕАЛЬНОЙ дате звонка (от новых к старым)
    calls.sort(key=lambda x: x["date"], reverse=True)
    
    return calls


@app.get("/api/audio/{week}/{company}/{manager}/{filename}")
def stream_audio(week: str, company: str, manager: str, filename: str):
    """Отдает файл для прослушивания"""
    file_path = BASE_DIR / week / company / manager / "audio" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

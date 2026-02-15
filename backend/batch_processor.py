from multiprocessing import Pool, cpu_count
import os
import json
from pathlib import Path
from backend.fast_transcriber import FastTranscriber
import time

def process_single_call(audio_path: str) -> dict:
    """Обрабатывает один звонок (для параллелизации)"""
    try:
        transcriber = FastTranscriber(model_name="tiny")
        result = transcriber.transcribe_with_speakers(audio_path)
        transcriber.cleanup()
        
        return {
            "file": os.path.basename(audio_path),
            "status": "success",
            "transcript": result["transcript"],
            "speakers": result["speakers"],
            "duration": result["duration"]
        }
    except Exception as e:
        return {
            "file": os.path.basename(audio_path),
            "status": "error",
            "error": str(e)
        }

def batch_transcribe(audio_dir: str, output_file: str, num_workers: int = 3):
    """
    Обрабатывает папку звонков параллельно
    
    Args:
        audio_dir: Папка с MP3 файлами
        output_file: Куда сохранить результаты (JSON)
        num_workers: Количество параллельных процессов (по умолчанию 3)
    """
    # Находим все MP3 файлы
    audio_files = sorted([
        str(p) for p in Path(audio_dir).glob("*.mp3")
    ])
    
    if not audio_files:
        print(f"❌ Не найдено MP3 файлов в {audio_dir}")
        return
    
    print(f"🎯 ПАКЕТНАЯ ОБРАБОТКА")
    print(f"="*70)
    print(f"📁 Папка: {audio_dir}")
    print(f"📊 Найдено файлов: {len(audio_files)}")
    print(f"⚙️  Параллельных процессов: {num_workers}")
    print(f"💾 Результат сохраним в: {output_file}")
    print(f"="*70)
    
    start_time = time.time()
    
    # Параллельная обработка
    with Pool(processes=num_workers) as pool:
        results = []
        for i, result in enumerate(pool.imap(process_single_call, audio_files), 1):
            results.append(result)
            status = "✅" if result["status"] == "success" else "❌"
            print(f"{status} {i}/{len(audio_files)}: {result['file']}")
    
    # Сохраняем результаты
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    
    print(f"\n{'='*70}")
    print(f"✅ ЗАВЕРШЕНО!")
    print(f"⏱️  Время: {elapsed:.1f} секунд ({elapsed/60:.1f} минут)")
    print(f"📊 Успешно: {success_count}/{len(audio_files)}")
    print(f"💾 Результаты: {output_file}")
    print(f"🚀 Скорость: {len(audio_files)/elapsed*60:.1f} звонков/минуту")
    print(f"{'='*70}")

if __name__ == "__main__":
    # Пример использования
    batch_transcribe(
        audio_dir="/root/sales-ai-agent/data/audio/SO",
        output_file="/root/sales-ai-agent/data/transcripts/SO_batch_fast.json",
        num_workers=3  # 3 процесса = оптимально для 4-core CPU
    )

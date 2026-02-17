# -*- coding: utf-8 -*-
import os
import glob
import json
import time
import torch
import torchaudio
import numpy as np
from faster_whisper import WhisperModel
from pyannote.audio import Model, Inference
from sklearn.cluster import KMeans
from dotenv import load_dotenv
from scipy.spatial.distance import cosine

load_dotenv()

BASE_DIR = "/root/sales-ai-agent/data/archive"
STATUS_FILE = "/root/sales-ai-agent/data/system_status.json"
VOICEPRINTS_FILE = "/root/sales-ai-agent/data/voiceprints.json"
HF_TOKEN = os.getenv("HF_TOKEN")
EMBEDDING_MODEL_ID = "pyannote/wespeaker-voxceleb-resnet34-LM"

def update_status(progress_msg):
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data["process_progress"] = progress_msg
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"Status error: {e}")

def load_voiceprints():
    if not os.path.exists(VOICEPRINTS_FILE):
        print("⚠️ Файл voiceprints.json не найден. Будут использоваться метки SPEAKER_XX.")
        return {}
    try:
        with open(VOICEPRINTS_FILE, 'r') as f:
            vps = json.load(f)
            print(f"🧠 Загружено {len(vps)} эталонов голоса: {list(vps.keys())}")
            return vps
    except Exception as e:
        print(f"❌ Ошибка чтения voiceprints.json: {e}")
        return {}

def identify_speakers(embeddings, labels, manager_name, voiceprints):
    """
    Определяет, кто из кластеров (0 или 1) является Менеджером, сравнивая с эталоном.
    """
    # 1. Проверяем, есть ли эталон для этого менеджера
    if manager_name not in voiceprints:
        return {0: "SPEAKER_00", 1: "SPEAKER_01"}

    # 2. Получаем вектора
    target_vector = np.array(voiceprints[manager_name])
    
    cluster_0 = embeddings[labels == 0]
    cluster_1 = embeddings[labels == 1]
    
    # Если какой-то кластер пуст (бывает на коротких записях)
    if len(cluster_0) == 0: return {0: "UNKNOWN", 1: "Менеджер"} # Скорее всего говорил только один
    if len(cluster_1) == 0: return {0: "Менеджер", 1: "UNKNOWN"}

    center_0 = np.mean(cluster_0, axis=0)
    center_1 = np.mean(cluster_1, axis=0)
    
    # 3. Считаем косинусное расстояние (меньше = лучше)
    dist_0 = cosine(target_vector, center_0)
    dist_1 = cosine(target_vector, center_1)
    
    print(f"   🔍 Идентификация {manager_name}: Dist(0)={dist_0:.3f}, Dist(1)={dist_1:.3f}")
    
    # 4. Принимаем решение
    if dist_0 < dist_1:
        # Кластер 0 ближе к эталону
        return {0: "Менеджер", 1: "Клиент"}
    else:
        # Кластер 1 ближе к эталону
        return {1: "Менеджер", 0: "Клиент"}

def diarize_audio(audio_path, segments, manager_name, voiceprints):
    try:
        # Загрузка модели эмбеддингов (кешируется)
        model = Model.from_pretrained(EMBEDDING_MODEL_ID, use_auth_token=HF_TOKEN)
        inference = Inference(model, window="whole")
        
        # Ручная загрузка аудио через torchaudio (обход багов Pyannote)
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Ресемплинг в 16кГц
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
            sample_rate = 16000
            
        # Конвертация в моно
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        embeddings = []
        valid_segments = []
        
        # Проходим по сегментам Whisper и извлекаем вектора
        for seg in segments:
            if seg.end - seg.start < 0.2: continue # Слишком короткие пропускаем
            try:
                start = int(seg.start * sample_rate)
                end = int(seg.end * sample_rate)
                if end > waveform.shape[1]: end = waveform.shape[1]
                
                chunk = waveform[:, start:end]
                # Получаем вектор
                emb = inference({"waveform": chunk, "sample_rate": sample_rate})
                if len(emb.shape) == 2: emb = emb[0]
                
                embeddings.append(emb)
                valid_segments.append(seg)
            except: pass

        if len(embeddings) < 2:
            # Если не удалось выделить 2 спикера -> считаем, что это один человек (или неизвестно)
            return [(s.start, s.end, "UNKNOWN", s.text) for s in segments]

        # Кластеризация (K-Means) на 2 спикера
        X = np.stack(embeddings)
        kmeans = KMeans(n_clusters=2, random_state=42).fit(X)
        labels = kmeans.labels_
        
        # Идентификация: Кто Менеджер?
        speaker_map = identify_speakers(X, labels, manager_name, voiceprints)
        
        # Формируем результат
        result = []
        for i, seg in enumerate(valid_segments):
            role = speaker_map[labels[i]]
            result.append((seg.start, seg.end, role, seg.text))
            
        return result

    except Exception as e:
        print(f"⚠️ Diarization error: {e}")
        # Fallback: возвращаем просто текст без ролей
        return [(s.start, s.end, "UNKNOWN", s.text) for s in segments]

def transcribe_all():
    print("🚀 Starting Smart Transcription (Whisper + Voiceprint)...")
    update_status("Загрузка моделей...")
    
    # Загружаем эталоны
    voiceprints = load_voiceprints()
    
    # Загружаем Whisper
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    
    all_files = []
    # Поиск новых файлов (нет .txt)
    for week in sorted(os.listdir(BASE_DIR), reverse=True):
        week_path = os.path.join(BASE_DIR, week)
        if not os.path.isdir(week_path): continue
        for company in os.listdir(week_path):
            comp_path = os.path.join(week_path, company)
            if not os.path.isdir(comp_path): continue
            for manager in os.listdir(comp_path):
                mgr_path = os.path.join(comp_path, manager)
                audio_dir = os.path.join(mgr_path, "audio")
                trans_dir = os.path.join(mgr_path, "transcripts")
                
                if not os.path.exists(audio_dir): continue
                os.makedirs(trans_dir, exist_ok=True)
                
                mp3s = glob.glob(os.path.join(audio_dir, "*.mp3"))
                for mp3 in mp3s:
                    fname = os.path.basename(mp3)
                    txt_name = fname.replace(".mp3", ".txt")
                    txt_path = os.path.join(trans_dir, txt_name)
                    
                    if not os.path.exists(txt_path):
                        all_files.append({
                            "audio": mp3,
                            "txt": txt_path,
                            "manager": manager,
                            "file": fname
                        })

    total = len(all_files)
    if total == 0:
        print("✅ Нет новых файлов для транскрибации.")
        return

    print(f"📂 Найдено {total} новых файлов.")
    
    for i, item in enumerate(all_files, 1):
        msg = f"Обработка {i}/{total}: {item['file']} ({item['manager']})..."
        print(msg)
        update_status(msg)
        
        try:
            # 1. Whisper (Текст + Таймкоды)
            segments, _ = model.transcribe(item["audio"], vad_filter=True, beam_size=5, language="ru")
            seg_list = list(segments)
            
            # 2. Диаризация + Идентификация (кто есть кто)
            diarized_segments = diarize_audio(item["audio"], seg_list, item["manager"], voiceprints)
            
            # 3. Сохранение результата
            with open(item["txt"], "w", encoding="utf-8") as f:
                for start, end, speaker, text in diarized_segments:
                    start_str = time.strftime('%M:%S', time.gmtime(start))
                    end_str = time.strftime('%M:%S', time.gmtime(end))
                    line = f"[{start_str} -> {end_str}] [{speaker}]: {text.strip()}\n"
                    f.write(line)
            
            print(f"   ✅ Готово: {item['txt']}")
            
        except Exception as e:
            print(f"❌ Ошибка {item['file']}: {e}")
            update_status(f"Ошибка: {e}")

    update_status("Готово")

if __name__ == "__main__":
    transcribe_all()

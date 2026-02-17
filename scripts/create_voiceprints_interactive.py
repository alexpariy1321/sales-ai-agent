# -*- coding: utf-8 -*-
import os
import json
import numpy as np
import torch
import torchaudio
from faster_whisper import WhisperModel
from pyannote.audio import Model, Inference
from sklearn.cluster import KMeans
from scipy.spatial.distance import cosine

# Конфиг
VOICEPRINTS_FILE = "/root/sales-ai-agent/data/voiceprints.json"
MODEL_ID = "pyannote/wespeaker-voxceleb-resnet34-LM"
HF_TOKEN = os.getenv("HF_TOKEN")

def get_embedding_model():
    print("🧠 Загрузка модели голоса (Pyannote)...")
    try:
        model = Model.from_pretrained(MODEL_ID, use_auth_token=HF_TOKEN)
        return Inference(model, window="whole")
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        exit(1)

def extract_embeddings(audio_path, inference):
    print(f"🎤 Обработка: {os.path.basename(audio_path)}")
    
    # 1. Whisper для сегментации
    print("   Запуск Whisper (medium)...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, vad_filter=True)
    seg_list = list(segments)
    
    if not seg_list:
        print("❌ Сегментов не найдено.")
        return None, None

    # 2. Pyannote Embedding
    print("   Извлечение векторов...")
    waveform, sample_rate = torchaudio.load(audio_path)
    
    # Ресемплинг
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = resampler(waveform)
        sample_rate = 16000
        
    # Моно
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    embeddings = []
    valid_segments = []

    for seg in seg_list:
        if seg.end - seg.start < 0.5: continue
        try:
            start = int(seg.start * sample_rate)
            end = int(seg.end * sample_rate)
            if end > waveform.shape[1]: end = waveform.shape[1]
            
            chunk = waveform[:, start:end]
            emb = inference({"waveform": chunk, "sample_rate": sample_rate})
            if len(emb.shape) == 2: emb = emb[0]
            
            embeddings.append(emb)
            valid_segments.append(seg)
        except: pass

    if len(embeddings) < 2:
        print("❌ Мало векторов.")
        return None, None
        
    return np.stack(embeddings), valid_segments

def save_voiceprint(manager_name, embedding):
    data = {}
    if os.path.exists(VOICEPRINTS_FILE):
        try:
            with open(VOICEPRINTS_FILE, 'r') as f:
                data = json.load(f)
        except: pass
    
    # Конвертируем numpy в список
    data[manager_name] = embedding.tolist()
    
    with open(VOICEPRINTS_FILE, 'w') as f:
        json.dump(data, f)
    print(f"✅ Эталон для '{manager_name}' сохранён/обновлён!")

def main():
    print("🎙️ МАСТЕР СОЗДАНИЯ ЭТАЛОНОВ ГОЛОСА")
    print(f"📂 Файл эталонов: {VOICEPRINTS_FILE}")
    
    inference = get_embedding_model()
    
    while True:
        print("\n" + "="*40)
        manager_name = input("Введите имя менеджера (или 'exit' для выхода): ").strip()
        if manager_name.lower() == 'exit': break
        if not manager_name: continue
        
        audio_path = input("Введите полный путь к mp3 файлу: ").strip()
        # Удаляем кавычки, если пользователь скопировал путь как "path"
        audio_path = audio_path.strip('"').strip("'")
        
        if not os.path.exists(audio_path):
            print("❌ Файл не найден!")
            continue
            
        embeddings, segments = extract_embeddings(audio_path, inference)
        
        if embeddings is None: continue

        # Кластеризация
        print("   Кластеризация (K-Means)...")
        kmeans = KMeans(n_clusters=2, random_state=42).fit(embeddings)
        labels = kmeans.labels_
        
        # Показываем примеры
        print("\n🔍 КТО ЕСТЬ КТО?")
        
        print("\n🔴 SPEAKER_0:")
        count = 0
        for i, seg in enumerate(segments):
            if labels[i] == 0:
                print(f"  [{seg.start:.1f}s]: {seg.text.strip()}")
                count += 1
                if count >= 3: break
                
        print("\n🔵 SPEAKER_1:")
        count = 0
        for i, seg in enumerate(segments):
            if labels[i] == 1:
                print(f"  [{seg.start:.1f}s]: {seg.text.strip()}")
                count += 1
                if count >= 3: break
        
        choice = input(f"\nКто из них {manager_name}? (0/1/skip): ").strip()
        
        if choice in ['0', '1']:
            target_label = int(choice)
            target_embs = embeddings[labels == target_label]
            voiceprint = np.mean(target_embs, axis=0)
            
            # Нормализация
            norm = np.linalg.norm(voiceprint)
            voiceprint = voiceprint / norm
            
            save_voiceprint(manager_name, voiceprint)
        else:
            print("⏩ Пропущено.")

if __name__ == "__main__":
    main()

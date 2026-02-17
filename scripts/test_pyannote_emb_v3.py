# -*- coding: utf-8 -*-
import os
import time
import torch
import torchaudio
import numpy as np
from pyannote.audio import Model
from pyannote.audio import Inference
from sklearn.cluster import KMeans
from faster_whisper import WhisperModel
from pyannote.core import Segment
import logging

logging.getLogger("speechbrain").setLevel(logging.ERROR)

# Настройки (твой файл)
AUDIO_FILE = "/root/sales-ai-agent/data/archive/2026-02-16_2026-02-22/UN/Ahmedshin_Dmitry/audio/dmitriy_akhmedshin_out_79503266027_2026_02_16-10_28_27_m7tj.mp3"
MODEL_ID = "pyannote/wespeaker-voxceleb-resnet34-LM"

def main():
    print("🚀 Запуск Pyannote Embedding V3 (Tensor Mode)...")
    start_time = time.time()

    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Файл не найден: {AUDIO_FILE}")
        exit(1)

    # 1. Whisper
    print("🎤 1. Whisper: Получаем сегменты...")
    model = WhisperModel("medium", device="cpu", compute_type="int8") 
    segments, _ = model.transcribe(AUDIO_FILE, vad_filter=True)
    seg_list = list(segments)
    print(f"   Найдено {len(seg_list)} сегментов.")

    if not seg_list:
        print("❌ Сегментов нет.")
        exit(1)

    # 2. Pyannote
    print("🧠 2. Pyannote: Загрузка модели...")
    try:
        embedding_model = Model.from_pretrained(MODEL_ID, use_auth_token=os.getenv("HF_TOKEN"))
    except Exception as e:
        print(f"⚠️ Ошибка загрузки модели: {e}")
        exit(1)
        
    inference = Inference(embedding_model, window="whole")
    
    # 3. Читаем аудио вручную
    print("🔊 3. Читаем аудио через torchaudio...")
    waveform, sample_rate = torchaudio.load(AUDIO_FILE)
    
    # Ресемплинг если нужно (Pyannote обычно хочет 16000)
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = resampler(waveform)
        sample_rate = 16000
        
    # Если стерео -> моно
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    print(f"   Аудио загружено: {waveform.shape} @ {sample_rate}Hz")

    embeddings = []
    valid_segments = []
    
    for i, seg in enumerate(seg_list):
        duration = seg.end - seg.start
        if duration < 0.2: continue
            
        try:
            # Вырезаем кусок тензора
            start_frame = int(seg.start * sample_rate)
            end_frame = int(seg.end * sample_rate)
            
            # Проверка границ
            if end_frame > waveform.shape[1]:
                end_frame = waveform.shape[1]
                
            chunk = waveform[:, start_frame:end_frame]
            
            # Передаем тензор в Pyannote
            # inference ожидает {"waveform": tensor, "sample_rate": int}
            emb = inference({"waveform": chunk, "sample_rate": sample_rate})
            
            if len(emb.shape) == 2:
                emb = emb[0]
                
            embeddings.append(emb)
            valid_segments.append(seg)
        except Exception as e:
            print(f"❌ Ошибка на сегменте {i}: {e}")
            if i > 5: break 

    print(f"   Обработано {len(valid_segments)} валидных сегментов.")

    if len(embeddings) < 2:
        print("❌ Мало данных.")
        exit(1)

    # 4. Кластеризация
    print("🧮 4. KMeans...")
    X = np.stack(embeddings)
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10).fit(X)
    labels = kmeans.labels_

    # 5. Вывод
    print("\n=== РЕЗУЛЬТАТ ===")
    lines = []
    for i, seg in enumerate(valid_segments):
        speaker = f"SPEAKER_{labels[i]}"
        line = f"[{seg.start:.1f}s] [{speaker}]: {seg.text.strip()}"
        print(line)
        lines.append(line)

    print(f"\n✅ Готово за {time.time() - start_time:.2f} сек!")

if __name__ == "__main__":
    main()

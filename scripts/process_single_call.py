# -*- coding: utf-8 -*-
import sys
import os
import json
import torch
import gc
import functools

# --- PATCH FOR PYTORCH 2.6+ & PYANNOTE ---
# WhisperX uses pyannote, which uses older serialization not compatible with weights_only=True
torch.load = functools.partial(torch.load, weights_only=False)
# -----------------------------------------

import whisperx

# Add root path to imports
sys.path.append("/root/sales-ai-agent")
from services.giga_service import analyze_transcript

def transcribe_audio(audio_path):
    device = "cpu"
    compute_type = "int8"
    
    print(f"Loading WhisperX for {audio_path}...")
    # Add vad_options to be explicit, though the patch above handles the core issue
    model = whisperx.load_model("base", device, compute_type=compute_type, language="ru")
    
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=16)
    
    del model
    gc.collect()
    
    text = " ".join([seg['text'] for seg in result['segments']])
    return text

def process_file(audio_path):
    if not os.path.exists(audio_path):
        print(f"File not found: {audio_path}")
        return

    base_dir = os.path.dirname(audio_path)
    manager_dir = os.path.dirname(base_dir)
    
    transcripts_dir = os.path.join(manager_dir, "transcripts")
    reports_dir = os.path.join(manager_dir, "report")
    os.makedirs(transcripts_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    filename = os.path.basename(audio_path)
    name_no_ext = os.path.splitext(filename)[0]
    
    transcript_path = os.path.join(transcripts_dir, f"{name_no_ext}.txt")
    report_path = os.path.join(reports_dir, f"{name_no_ext}.md")
    
    # 1. Transcription
    if os.path.exists(transcript_path):
        print(f"Transcript exists: {transcript_path}")
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
    else:
        print("Starting transcription...")
        transcript_text = transcribe_audio(audio_path)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        print("Transcription done.")

    # 2. Analysis
    print("Sending to GigaChat Pro...")
    analysis = analyze_transcript(transcript_text)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(analysis)
    
    print(f"DONE! Report saved: {report_path}")
    print("-" * 20)
    print(analysis[:500] + "...\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        target_file = "/root/sales-ai-agent/data/archive/2026-02-02_2026-02-06/UN/Ahmedshin_Dmitry/audio/dmitriy_akhmedshin_out_79178549105_2026_02_06-16_44_32_l6ml.mp3"
        
    process_file(target_file)

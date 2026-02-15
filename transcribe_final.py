import os, requests, json, time

def load_config():
    c = {}
    with open('/root/sales-ai-agent/.env') as f:
        for l in f:
            if '=' in l:
                k, v = l.strip().split('=', 1)
                c[k] = v.strip('"').strip("'")
    return c

def process_file(file_path, key, proxy):
    # 1. Загрузка (File API)
    up_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={key}"
    headers = {"X-Goog-Upload-Protocol": "multipart"}
    files = {
        'metadata': (None, json.dumps({"file": {"display_name": os.path.basename(file_path)}}), 'application/json'),
        'file': (os.path.basename(file_path), open(file_path, 'rb'), 'audio/mp3')
    }
    r = requests.post(up_url, headers=headers, files=files, proxies=proxy, timeout=120).json()
    f_uri, f_name = r['file']['uri'], r['file']['name']

    # 2. Ожидание
    check_url = f"https://generativelanguage.googleapis.com/v1beta/{f_name}?key={key}"
    while requests.get(check_url, proxies=proxy).json().get('state') != 'ACTIVE':
        time.sleep(3)

    # 3. Транскрибация через "Live" модель (Flash-Lite)
    # Эта модель меньше "галлюцинирует" на шуме
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite-001:generateContent?key={key}"
    
    prompt = (
        "Ты — точный ИИ-стенографист. Твоя задача: дословно переписать разговор. "
        "Правила:\n"
        "1. Если в записи нет человеческой речи (гудки, музыка, тишина), выведи только одну фразу: '[НЕТ РЕЧИ]'.\n"
        "2. Если речь есть, пиши в формате 'Менеджер: текст' и 'Клиент: текст'.\n"
        "3. Не добавляй отсебятины и выводов."
    )
    
    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"file_data": {"mime_type": "audio/mp3", "file_uri": f_uri}}
        ]}],
        "generationConfig": {
            "temperature": 0.1,  # Минимальная температура = минимум мусора
            "topP": 0.95,
            "topK": 40
        }
    }
    
    res = requests.post(gen_url, json=payload, proxies=proxy, timeout=120).json()
    
    if 'candidates' in res:
        return res['candidates'][0]['content']['parts'][0]['text']
    return "[ОШИБКА ГЕНЕРАЦИИ]"

def run():
    conf = load_config()
    proxy = {"http": conf['PROXY_URL'], "https": conf['PROXY_URL']}
    base_audio = '/root/sales-ai-agent/data/audio'
    base_text = '/root/sales-ai-agent/data/transcripts'
    
    for mgr in ['Garyaev_Maxim', 'Popov_Denis', 'Ahmedshin_Dmitry']:
        m_dir = os.path.join(base_audio, mgr)
        t_dir = os.path.join(base_text, mgr)
        if not os.path.exists(m_dir): continue
        os.makedirs(t_dir, exist_ok=True)
        
        print(f"\n--- Обработка {mgr} (Lite Model) ---")
        for f in sorted(os.listdir(m_dir)):
            if not f.endswith('.mp3'): continue
            # Увеличим порог фильтрации мусора до 60Кб
            if os.path.getsize(os.path.join(m_dir, f)) < 60000: continue
            
            out_f = os.path.join(t_dir, f.replace('.mp3', '.txt'))
            if os.path.exists(out_f): continue
            
            print(f"Файл: {f}", end=" | ")
            try:
                text = process_file(os.path.join(m_dir, f), conf['GEMINI_API_KEY'], proxy)
                with open(out_f, 'w', encoding='utf-8') as out: out.write(text)
                print("ОК")
                time.sleep(2)
            except Exception as e:
                print(f"ОШИБКА: {e}")

if __name__ == "__main__":
    run()

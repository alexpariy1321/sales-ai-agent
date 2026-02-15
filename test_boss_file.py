import os, requests, json, time

def load_config():
    c = {}
    with open('/root/sales-ai-agent/.env') as f:
        for l in f:
            if '=' in l:
                k, v = l.strip().split('=', 1)
                c[k] = v.strip('"').strip("'")
    return c

def run_test():
    conf = load_config()
    key = conf['GEMINI_API_KEY']
    proxy = {"http": conf['PROXY_URL'], "https": conf['PROXY_URL']}
    file_path = "/root/sales-ai-agent/data/audio/Garyaev_Maxim/ivanova_elena_aleksandrovna_out_74912500888_2026_02_05-10_29_59_cbeg.mp3"
    
    print("--- 1. Загрузка (v1alpha) ---")
    up_url = f"https://generativelanguage.googleapis.com/upload/v1alpha/files?key={key}"
    headers = {"X-Goog-Upload-Protocol": "multipart"}
    files = {
        'metadata': (None, json.dumps({"file": {"display_name": "ULTIMATE_TEST"}}), 'application/json'),
        'file': (os.path.basename(file_path), open(file_path, 'rb'), 'audio/mp3')
    }
    r = requests.post(up_url, headers=headers, files=files, proxies=proxy).json()
    f_uri, f_name = r['file']['uri'], r['file']['name']

    print("--- 2. Ожидание ---")
    check_url = f"https://generativelanguage.googleapis.com/v1alpha/{f_name}?key={key}"
    while requests.get(check_url, proxies=proxy).json().get('state') != 'ACTIVE':
        time.sleep(3)

    print("--- 3. Транскрибация (Gemini 2.0 Flash Lite) ---")
    # Используем модель из твоего списка через v1alpha
    gen_url = f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-2.0-flash-lite-001:generateContent?key={key}"
    
    payload = {
        "contents": [{"parts": [
            {"text": "Сделай транскрибацию звонка. Раздели диалог: Менеджер и Клиент."},
            {"file_data": {"mime_type": "audio/mp3", "file_uri": f_uri}}
        ]}],
        "safetySettings": [{"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}]
    }
    
    res = requests.post(gen_url, json=payload, proxies=proxy).json()
    
    if 'candidates' in res:
        print("\n=== ПОБЕДА! РЕЗУЛЬТАТ ===\n")
        print(res['candidates'][0]['content']['parts'][0]['text'])
    else:
        print("\nОШИБКА API:")
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    run_test()

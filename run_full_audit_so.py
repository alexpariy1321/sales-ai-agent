import os, requests, uuid, warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
# Загружаем ключи из .env в текущей папке
load_dotenv('.env')

# ОТНОСИТЕЛЬНЫЙ ПУТЬ (исправлено)
BASE_PATH = "data/archive/2026-02-02_2026-02-06/SO/Volkov_Ivan"
TRANSCRIPT_DIR = os.path.join(BASE_PATH, "transcripts")
REPORT_DIR = os.path.join(BASE_PATH, "report")

def get_token():
    creds = os.getenv('GIGACHAT_CREDENTIALS')
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {creds}'
    }
    res = requests.post(url, data={'scope': 'GIGACHAT_API_PERS'}, headers=headers, verify=False)
    return res.json().get('access_token')

def main():
    if not os.path.exists(REPORT_DIR): os.makedirs(REPORT_DIR)
    token = get_token()
    if not token:
        print("Ошибка: Токен не получен. Проверьте .env")
        return

    # Проверяем наличие транскриптов
    if not os.path.exists(TRANSCRIPT_DIR):
        print(f"Ошибка: Папка {TRANSCRIPT_DIR} не найдена!")
        return

    files = [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith('.txt')]
    print(f"Найдено звонков для анализа: {len(files)}")

    for f in files:
        base_name = os.path.splitext(f)[0]
        report_file = os.path.join(REPORT_DIR, f"{base_name}.md")
        if os.path.exists(report_file): continue

        print(f"Анализ {f}...", end=" ", flush=True)
        with open(os.path.join(TRANSCRIPT_DIR, f), 'r', encoding='utf-8') as file:
            txt = file.read()[:5000]
            res = requests.post('https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
                json={
                    'model': 'GigaChat-Pro', 
                    'messages': [
                        {'role': 'system', 'content': 'Ты жесткий аудитор. Оцени звонок Волкова по структуре Куркина (Суть, Оценка 0-10, Ошибки, Договоренность).'},
                        {'role': 'user', 'content': txt}
                    ]
                },
                headers={'Authorization': f'Bearer {token}'}, verify=False)
            
            if res.status_code == 200:
                with open(report_file, 'w', encoding='utf-8') as out:
                    out.write(res.json()['choices'][0]['message']['content'])
                print("OK")
            else:
                print(f"Ошибка API: {res.status_code}")

if __name__ == "__main__":
    main()

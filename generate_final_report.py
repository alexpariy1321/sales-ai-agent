import os, requests, uuid
from dotenv import load_dotenv

load_dotenv('.env')
BASE_PATH = "data/archive/2026-02-02_2026-02-06/SO/Volkov_Ivan"
REPORT_DIR = os.path.join(BASE_PATH, "report")
FINAL_FILE = os.path.join(BASE_PATH, "FINAL_AUDIT_VOLKOV_FEB.md")

def main():
    creds = os.getenv('GIGACHAT_CREDENTIALS')
    token_res = requests.post('https://ngw.devices.sberbank.ru:9443/api/v2/oauth', 
                             data={'scope': 'GIGACHAT_API_PERS'}, 
                             headers={'RqUID': str(uuid.uuid4()), 'Authorization': f'Basic {creds}'}, verify=False)
    token = token_res.json().get('access_token')

    reports = []
    for f in os.listdir(REPORT_DIR):
        if f.endswith('.md'):
            with open(os.path.join(REPORT_DIR, f), 'r') as file:
                reports.append(file.read())

    print("Собираем финальный отчет для Димы Куркина...")
    full_ctx = "\n\n---\n\n".join(reports)[:15000]
    res = requests.post('https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
        json={'model': 'GigaChat-Pro', 'messages': [{'role': 'user', 'content': f"Напиши сводный аудит за неделю для РОПа. Используй эти данные: {full_ctx}"}]},
        headers={'Authorization': f'Bearer {token}'}, verify=False)

    with open(FINAL_FILE, 'w', encoding='utf-8') as f:
        f.write(res.json()['choices'][0]['message']['content'])
    print(f"Готово! Файл: {FINAL_FILE}")

if __name__ == "__main__": main()

# -*- coding: utf-8 -*-
import os
import json
from gigachat import GigaChat
from dotenv import load_dotenv

# Load .env
load_dotenv("/root/sales-ai-agent/.env")

CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
DEFAULT_PROMPT_FILE = "/root/sales-ai-agent/data/current_prompt.json"

def get_current_prompt():
    if os.path.exists(DEFAULT_PROMPT_FILE):
        try:
            with open(DEFAULT_PROMPT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("prompt", "")
        except Exception:
            pass
    
    # Default prompt if file not found
    return """
    Ты — эксперт по анализу телефонных продаж. Проанализируй этот диалог менеджера.
    Оцени работу по 10-балльной шкале.
    Выдели 3 главные ошибки и 3 удачных момента.
    Проверь, была ли попытка закрытия сделки.
    """

def analyze_transcript(transcript_text, custom_prompt=None):
    if not CREDENTIALS:
        return "Error: GIGACHAT_CREDENTIALS not found in .env"

    system_prompt = custom_prompt if custom_prompt else get_current_prompt()
    
    # Truncate text to avoid limits (leaving space for prompt)
    truncated_text = transcript_text[:18000] 

    try:
        with GigaChat(credentials=CREDENTIALS, verify_ssl_certs=False, scope="GIGACHAT_API_PERS") as giga:
            payload = {
                "model": "GigaChat-Pro",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": truncated_text}
                ],
                "temperature": 0.1
            }
            
            response = giga.chat(payload)
            return response.choices[0].message.content
            
    except Exception as e:
        return f"Error GigaChat analysis: {str(e)}"

if __name__ == "__main__":
    test_text = "Менеджер: Алло, здравствуйте. Клиент: Добрый день, мне нужен битум."
    print("Testing GigaChat analysis...")
    print(analyze_transcript(test_text))

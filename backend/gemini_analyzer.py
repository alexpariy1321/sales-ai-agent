from google import genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

def analyze_call_with_gemini(transcript_with_speakers: str, manager_name: str = "Менеджер") -> dict:
    """
    Анализирует транскрипцию со спикерами через Gemini API
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "text": "GEMINI_API_KEY not found in .env",
            "rating": None,
            "model": "gemini-2.0-flash-exp",
            "provider": "google",
            "status": "error",
            "error": "API key missing"
        }
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Форматируем транскрипцию
        if isinstance(transcript_with_speakers, list):
            formatted = "\n".join([
                f"{seg.get('speaker', 'UNKNOWN')}: {seg.get('text', '')}"
                for seg in transcript_with_speakers
            ])
        else:
            formatted = transcript_with_speakers
        
        # Ограничиваем длину (API имеет лимиты)
        formatted = formatted[:4000]
        
        # Промпт на английском чтобы избежать проблем с кодировкой
        prompt = f"""
You are an expert in sales of construction materials (sand, gravel).
Analyze this sales call by manager {manager_name}.

TRANSCRIPT WITH SPEAKERS:
{formatted}

EVALUATE ON 10-POINT SCALE:
1. Contact establishment (greeting, introduction) - 0-2 points
2. Needs identification (asking questions) - 0-2 points  
3. Product presentation - 0-2 points
4. Objection handling - 0-2 points
5. Next step agreement - 0-2 points

RESPONSE FORMAT:
**Rating:** X/10

**Critical Errors:**
- [list in Russian]

**What was done well:**
- [list in Russian]

**Recommendations:**
- [list in Russian]

**Next step agreement:** Yes/No
"""
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        analysis_text = response.text
        
        # Извлекаем оценку
        rating_match = re.search(r'Rating.*?(\d+)', analysis_text, re.IGNORECASE)
        if not rating_match:
            rating_match = re.search(r'(\d+)/10', analysis_text)
        
        rating = int(rating_match.group(1)) if rating_match else None
        
        return {
            "text": analysis_text,
            "rating": rating,
            "model": "gemini-2.0-flash-exp",
            "provider": "google",
            "status": "success"
        }
    except Exception as e:
        return {
            "text": f"Error: {str(e)}",
            "rating": None,
            "model": "gemini-2.0-flash-exp",
            "provider": "google",
            "status": "error",
            "error": str(e)
        }

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_search():
    keys_str = os.getenv('GEMINI_API_KEY', '')
    api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
    
    if not api_keys:
        print("ERROR: No API keys found.")
        return

    client = genai.Client(api_key=api_keys[0])
    model_name = 'gemini-flash-latest'
    
    system_prompt = "You are a legal expert. Return JSON."
    lang = 'English'
    localized_system_prompt = f"{system_prompt}\n\nIMPORTANT: ALL ANALYSIS AND DESCRIPTIONS WITHIN THE JSON MUST BE IN {lang}."
    query = "ipc 433"
    prompt = f"Analyze legal query: {query}. Respond in STRICT JSON format."
    
    print(f"Testing model: {model_name}")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=localized_system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        print("Response successful!")
        print(response.text)
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_search()

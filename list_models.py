import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    keys_str = os.getenv('GEMINI_API_KEY', '')
    api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
    client = genai.Client(api_key=api_keys[0])
    
    print("Available Gemini Models:")
    for model in client.models.list():
        print(f"Name: {model.name}, Supported Actions: {model.supported_actions}")

if __name__ == "__main__":
    list_models()

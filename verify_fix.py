import os
import sys
# Add current directory to path so we can import services
sys.path.append(os.getcwd())

from services.gemini_service import gemini_service

def verify_fix():
    print(f"Testing with model: {gemini_service.model_name}")
    print(f"Number of API keys: {len(gemini_service.api_keys)}")
    
    query = "ipc 433"
    system_prompt = "You are a legal expert. Return JSON."
    
    print(f"Querying: {query}...")
    result = gemini_service.search_section(query, system_prompt)
    
    if isinstance(result, list) and len(result) > 0:
        first_res = result[0]
        if first_res.get("section") == "Error":
            print("FAIL: Search still failing.")
            print(first_res)
        else:
            print("SUCCESS: Search working!")
            print(f"Section: {first_res.get('section')}")
            print(f"Title: {first_res.get('title')}")
    elif isinstance(result, dict) and result.get("section") == "Error":
        print("FAIL: Search still failing.")
        print(result)
    else:
        print("SUCCESS: Search working (single object result)!")
        print(result)

if __name__ == "__main__":
    verify_fix()

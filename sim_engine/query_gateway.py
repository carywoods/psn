import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPEN_WEBUI_KEY = os.getenv("OPEN_WEBUI_KEY")
GATEWAY_URL = os.getenv("GATEWAY_URL")
MODEL_ID = "glm-4.7-flash:latest"

def query_metabolic_logic():
    url = f"{GATEWAY_URL}/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPEN_WEBUI_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """
    As a metabolic engineering expert focusing on Saccharomyces cerevisiae and the Yeast-GEM (Yeast9) model:
    1. Identify the standard exchange reaction IDs for aerobic glucose fermentation in Yeast9.
    2. Provide default flux bounds (Lower Bound, Upper Bound) for high-yield ethanol production in this model.
    3. Return the IDs and bounds in a clear JSON-like format suitable for implementation in COBRApy.
    """
    
    data = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(content)
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    query_metabolic_logic()

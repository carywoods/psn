import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPEN_WEBUI_KEY = os.getenv("OPEN_WEBUI_KEY")
GATEWAY_URL = os.getenv("GATEWAY_URL")
# Use the model as per the existing script
MODEL_ID = "glm-4.7-flash:latest"

def query_goebl_logic():
    url = f"{GATEWAY_URL}/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPEN_WEBUI_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """
    The Xylogenics founders were trained in the Mark Goebl Lab at IU. 
    Focus on the CDC34/CDC53/SCF complex research. 
    a. How does the degradation of Sic1 and Gcn4 regulate S-phase entry and amino acid biosynthesis? 
    b. Translate this into a 'Regulatory Penalty' for the PSN engine: If the cell is in G1-arrest, how much should the ATP maintenance (NGAM) increase to account for proteasomal activity?
    """
    
    data = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    print(f"Querying Gateway at {GATEWAY_URL}...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return content
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception: {e}"

if __name__ == "__main__":
    result = query_goebl_logic()
    print(result)

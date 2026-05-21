import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPEN_WEBUI_KEY = os.getenv("OPEN_WEBUI_KEY")
GATEWAY_URL = os.getenv("GATEWAY_URL")

def verify_gateway_connection():
    """Tests the handshake with the Open WebUI gateway."""
    print(f"Testing connection to Gateway: {GATEWAY_URL}")
    
    headers = {
        "Authorization": f"Bearer {OPEN_WEBUI_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Example endpoint for Open WebUI models or health check
        # Adjusting to a common base check or models list
        response = requests.get(f"{GATEWAY_URL}/api/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("Successfully connected to Gateway Node (42).")
            print(f"Available models: {response.json()}")
        else:
            print(f"Failed to connect. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    verify_gateway_connection()

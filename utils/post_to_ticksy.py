import requests
import os
from dotenv import load_dotenv

load_dotenv()

TICKSY_DOMAIN = os.getenv("TICKSY_DOMAIN")
TICKSY_API_KEY = os.getenv("TICKSY_API_KEY")
TICKSY_API_URL = f"https://api.ticksy.com/v1/{TICKSY_DOMAIN}/{TICKSY_API_KEY}"

def post_to_ticksy(ticket_id: str, message: str) -> dict:
    api_key = os.getenv("TICKSY_API_KEY")
    domain = os.getenv("TICKSY_DOMAIN")

    url = f"https://api.ticksy.com/v1/{domain}/{api_key}"
    
    payload = {
        "action": "new_ticket_comment",
        "ticket_id": ticket_id,
        "comment": message,
        "private": "false"
    }

    #print( payload )

    try:
        r = requests.post(url, data=payload)
        return {"status": "ok", "response": r.text} if r.ok else {"status": "error", "response": r.text}
    except Exception as e:
        return {"status": "error", "response": str(e)}

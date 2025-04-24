import requests
import os
from dotenv import load_dotenv

load_dotenv()

TICKSY_DOMAIN = os.getenv("TICKSY_DOMAIN")
TICKSY_API_KEY = os.getenv("TICKSY_API_KEY")
TICKSY_API_URL = f"https://api.ticksy.com/v1/{TICKSY_DOMAIN}/{TICKSY_API_KEY}"

def post_to_ticksy(ticket_id: str, message: str, close_ticket: bool) -> dict:
    api_key = os.getenv("TICKSY_API_KEY")
    domain = os.getenv("TICKSY_DOMAIN")

    url = f"https://api.ticksy.com/v1/{domain}/{api_key}"
    
    payload = {
        "action": "new_ticket_comment",
        "ticket_id": ticket_id,
        "comment": message,
        "private": "false"
    }

    # Post ticket
    try:
        r = requests.post(url, data=payload)

        if close_ticket:
            close_ticksy_ticket(ticket_id=ticket_id)

        return {"status": "ok", "response": r.text} if r.ok else {"status": "error", "response": r.text}
    except Exception as e:
        return {"status": "error", "response": str(e)}


def close_ticksy_ticket(ticket_id: str):
    api_key = os.getenv("TICKSY_API_KEY")
    domain = os.getenv("TICKSY_DOMAIN")

    url = f"https://api.ticksy.com/v1/{domain}/{api_key}"
    close_payload = {
        "action": "close_ticket",
        "ticket_id": ticket_id
    }
    try:
        r_close = requests.post(url, data=close_payload)
        print("Ticket closed") if r_close.ok else print("Failed to close ticket:", r_close.text)
    except Exception as e:
        print("Error closing ticket:", str(e))


    

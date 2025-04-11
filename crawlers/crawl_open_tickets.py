import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from parent directory explicitly
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

TICKSY_DOMAIN = os.getenv("TICKSY_DOMAIN")
TICKSY_API_KEY = os.getenv("TICKSY_API_KEY")
BASE_API_URL = f"https://api.ticksy.com/v1/{TICKSY_DOMAIN}/{TICKSY_API_KEY}"

os.makedirs("data/crawled", exist_ok=True)

def fetch_open_tickets():
    url = f"{BASE_API_URL}/open-tickets.json"
    print(f"Fetching tickets from {url}")

    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch tickets: {response.status_code}")
        return []

    return response.json()

def save_tickets(data, filename="data/crawled/open_tickets.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved recent open tickets to {filename}")

def main():
    tickets = fetch_open_tickets()
    if tickets:
        save_tickets(tickets)
    else:
        print("No tickets fetched.")

if __name__ == "__main__":
    main()
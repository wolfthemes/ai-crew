# tools/preprocess_tickets.py
import sys
import os
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.ticket_utils import preprocess_closed_tickets, save_preprocessed_closed_tickets

def run_preprocessing():
    try:
        print("📦 Preprocessing closed tickets...")
        subprocess.run(["python", "crawlers/crawl_closed_tickets.py"], check=True)
        closed_tickets = preprocess_closed_tickets(filepath="data/crawled/closed_tickets.json")
        save_preprocessed_closed_tickets(closed_tickets)
        print(f"✅ {len(closed_tickets)} tickets saved to closed_tickets.json")

    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_preprocessing()

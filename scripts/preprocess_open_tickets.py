# scripts/preprocess_tickets.py
import sys
import os
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.ticket_utils import preprocess_open_tickets, save_preprocessed_open_tickets

def run_preprocessing():
    try:
        print("📦 Preprocessing open tickets...")
        subprocess.run(["python", "crawlers/crawl_open_tickets.py"], check=True)
        open_tickets = preprocess_open_tickets(filepath="data/crawled/open_tickets.json")
        save_preprocessed_open_tickets(open_tickets, output_path="data/dynamic/tickets/open_tickets.json")
        print(f"✅ {len(open_tickets)} tickets saved to open_tickets.json")

    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_preprocessing()

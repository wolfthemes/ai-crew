# tools/preprocess_tickets.py
import sys
import os
import subprocess
from utils.ticket_utils import preprocess_open_tickets, save_preprocessed_open_tickets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_preprocessing():
    try:
        print("📦 Preprocessing all open tickets...")
        subprocess.run(["python", "crawlers/crawl_open_tickets.py"], check=True)

        tickets = preprocess_open_tickets(filepath="data/crawled/open_tickets.json")

        save_preprocessed_open_tickets(tickets, output_path="data/dynamic/tickets/preprocessed_tickets.json")
        print(f"✅ {len(tickets)} tickets saved to preprocessed_tickets.json")

    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_preprocessing()

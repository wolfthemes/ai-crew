# scripts/generate_reply_drafts.py
# cd ~/wolfthemes-dev/ai-crew && source .venv/scripts/activate && python scripts/generate_reply_drafts.py
import shutil
import sys
import json
import os
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.ticket_utils import preprocess_open_tickets, save_preprocessed_open_tickets
from crews.support_crew import support_crew_with_research

# Import utility functions

# Constants
DB_PATH = "data/db/open_tickets.db"
CRAWLED_PATH = "data/crawled/open_tickets.json"
PREPROCESSED_PATH = "data/dynamic/tickets/open_tickets.json"
DRAFT_PATH = "data/dynamic/editor"

def run_preprocessing():
    """Run the preprocessing step to prepare ticket data"""
    try:
        print("📦 Preprocessing open tickets...")
        subprocess.run(["python", "crawlers/crawl_open_tickets.py"], check=True)
        open_tickets = preprocess_open_tickets(filepath=CRAWLED_PATH)
        save_preprocessed_open_tickets(open_tickets)
        print(f"✅ {len(open_tickets)} tickets preprocessed and saved to {PREPROCESSED_PATH}")
        return True
    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def load_tickets_from_json(json_path):
    """Load the preprocessed tickets from JSON file"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)["open_tickets"]

def main():
    """Main function to preprocess tickets, generate reply and save into drafts"""
    print("🔄 Starting combined ticket preprocessing, generate reply, and save drafts...")
    
    # 1. Preprocess tickets
    if not run_preprocessing():
        print("❌ Preprocessing failed. Database insertion skipped.")
        return
        
    # 2. Load preprocessed tickets
    if not os.path.exists(PREPROCESSED_PATH):
        print(f"❌ Preprocessed JSON file not found: {PREPROCESSED_PATH}")
        return
    
    # 3. Empty the draft folder
    if os.path.exists(DRAFT_PATH):
        for item in os.listdir(DRAFT_PATH):
            item_path = os.path.join(DRAFT_PATH, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        # Create the directory if it doesn't exist
        os.makedirs(DRAFT_PATH, exist_ok=True)
        
    tickets = load_tickets_from_json(PREPROCESSED_PATH)

    # 4. Loop through each ticket and save reply
    for ticket in tickets:
        print(f"Ticket #{ticket['id']}: {ticket['subject']}")
        
        result = support_crew_with_research(ticket["last_message"], instruction="", ticket_id=ticket['id'])
        # Extract the actual string content from the TaskOutput object
        if hasattr(result["reply"], "output"):
            reply_html = result["reply"].output
        elif isinstance(result["reply"], str):
            reply_html = result["reply"]
        else:
            # If it's a TaskOutput object without an output attribute, try to convert it to string
            reply_html = str(result["reply"])

        # Save in draft DRAFT_PATH/draft_ticket['id']
        draft_file = os.path.join(DRAFT_PATH, f"draft_{ticket['id']}")
        with open(draft_file, "w", encoding="utf-8") as f:
            f.write(reply_html)

    # Step 3: Generate replies
    print("✅ Drafts generated successfully!")

if __name__ == "__main__":
    main()
# cd ~/wolfthemes-dev/ai-crew && source .venv/scripts/activate && python scripts/closed_tickets_etl.py

import sys
import os
import json
import sqlite3
import shutil
from pathlib import Path
import subprocess
from datetime import date, datetime, timedelta

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import utility functions
from utils.ticket_utils import preprocess_closed_tickets, save_preprocessed_closed_tickets
from utils.post_to_ticksy import close_ticksy_ticket
from utils.helpers import setup_logging
logger = setup_logging()
today = date.today().strftime("%Y-%m-%d")

# Constants
DB_PATH = "data/db/closed_tickets.db"
CRAWLED_PATH = "data/crawled/closed_tickets.json"
PREPROCESSED_PATH = "data/dynamic/tickets/closed_tickets.json"
BACKUP_DIR = r"G:\My Drive\DBBackup\ai-crew"
STALE_TICKETS_DAYS_LIMIT = 7

def close_stale_tickets():
    """Close tickets that don't need response and that are open since more than 7 days"""

    try:
        print("📦 Crawling open tickets...")
        subprocess.run(["python", "crawlers/crawl_open_tickets.py"], check=True)
        filepath = 'data/crawled/open_tickets.json'
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        for t in data.get("open-tickets", []):
            # Skip invalid or unhelpful tickets (non-theme-cateogry, deleted customer )
            stale = int(t.get("needs_response", "1")) == 0
            ticket_id = t.get("ticket_id")
            comments = t.get( "ticket_comments" )
            today_date = datetime.today().date()
            last_comment_time_stamp = comments[0]["time_stamp"]
            try:
                last_comment_date = datetime.strptime(last_comment_time_stamp, "%Y-%m-%d %H:%M:%S").date()
                ticket_age = (today_date - last_comment_date).days
              
                # Close ticket older than X days
                if stale and ticket_age > STALE_TICKETS_DAYS_LIMIT:
                    print(f"🚮 Closing ticket {ticket_id} ({ticket_age} days old)")
                    close_ticksy_ticket(ticket_id=ticket_id)
            
            except Exception as e:
                print(f"⚠️ Failed to parse date for ticket {ticket_id}: {e}")
        return True

    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_preprocessing():
    """Run the preprocessing step to prepare ticket data"""
    try:
        print("📦 Preprocessing closed tickets...")
        subprocess.run(["python", "crawlers/crawl_closed_tickets.py"], check=True)
        closed_tickets = preprocess_closed_tickets(filepath=CRAWLED_PATH)
        save_preprocessed_closed_tickets(closed_tickets)
        print(f"✅ {len(closed_tickets)} tickets preprocessed and saved to {PREPROCESSED_PATH}")
        return True
    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def load_tickets_from_json(json_path):
    """Load the preprocessed tickets from JSON file"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)["closed_tickets"]

def ensure_tables(cursor):
    """Create the necessary database tables if they don't exist"""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS closed_tickets (
        ticket_id TEXT PRIMARY KEY,
        theme TEXT,
        builder TEXT,
        formatted_text_thread TEXT,
        full_thread_summary TEXT,
        created_at TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_insights (
        ticket_id TEXT PRIMARY KEY,
        match_source TEXT,
        ticket_summary TEXT,
        solution_summary TEXT,
        created_at TEXT
    );
    """)

def insert_into_db(tickets, db_path):
    """Insert the preprocessed tickets into the database"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    ensure_tables(cursor)
    
    for ticket in tickets:
        cursor.execute("""
        INSERT OR REPLACE INTO closed_tickets (
            ticket_id, theme, builder, formatted_text_thread,
            full_thread_summary, created_at
        ) VALUES (?, ?, ?, ?, ?, ?);
        """, (
            ticket["id"],
            ticket.get("theme", ""),
            ticket.get("builder", ""),
            ticket.get("formatted_text_thread", ""),
            ticket.get("full_thread_summary", ""),
            ticket.get("time_stamp", "")
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(tickets)} tickets into {db_path}")

def backup_database(db_path, backup_dir):
    """Create a backup of the database in the specified backup directory"""
    try:
        # Make sure the backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"closed_tickets_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Also create a copy with a fixed name (latest version)
        latest_backup_path = os.path.join(backup_dir, "closed_tickets_latest.db")
        shutil.copy2(db_path, latest_backup_path)
        
        print(f"✅ Database backed up to {backup_path}")
        print(f"✅ Latest version backed up to {latest_backup_path}")
        return True
    except Exception as e:
        print(f"❌ Database backup failed: {str(e)}")
        return False

def main():
    """Main function to preprocess tickets, insert them into the database, and create a backup"""
    print("🔄 Starting combined ticket preprocessing, DB insertion, and backup...")

    
    logger.info(f"Starting Closed tickets ETL for {today}")

    # Step 1: Close stale tickets
    if not close_stale_tickets():
        print("❌ Closing stale tickets failed. Task skipped")
        return
    else:
        logger.info(f"✅ Stale tickets closed")
    
    # Step 2: Preprocess tickets
    if not run_preprocessing():
        #logger.error(f"❌ Preprocessing failed. Database insertion skipped.")
        print("❌ Preprocessing failed. Database insertion skipped.")
        return
    else:
        logger.info(f"✅ Closed tickets crawled")
    
    # Step 3: Load preprocessed tickets
    if not os.path.exists(PREPROCESSED_PATH):
        #logger.error(f"❌ Preprocessed JSON file not found: {PREPROCESSED_PATH}")
        print(f"❌ Preprocessed JSON file not found: {PREPROCESSED_PATH}")
        return
    else:
        logger.info(f"✅ Closed tickets preprocessed")
        
    tickets = load_tickets_from_json(PREPROCESSED_PATH)
    
    # Step 4: Insert tickets into database
    insert_into_db(tickets, DB_PATH)
    
    # Step 5: Backup the database
    if backup_database(DB_PATH, BACKUP_DIR):
        logger.info(f"✅ Database backup completed successfully!")
        print("✅ Database backup completed successfully!")
    else:
        logger.error(f"⚠️ Process completed but database backup failed.")
        print("⚠️ Process completed but database backup failed.")
        
    logger.info(f"✅ Combined process completed successfully!")
    print("✅ Combined process completed successfully!")

if __name__ == "__main__":
    main()
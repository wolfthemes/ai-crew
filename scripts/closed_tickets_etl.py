import sys
import os
import json
import sqlite3
import shutil
from pathlib import Path
import subprocess
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import utility functions
from utils.ticket_utils import preprocess_closed_tickets, save_preprocessed_closed_tickets

# Constants
DB_PATH = "data/db/closed_tickets.db"
CRAWLED_PATH = "data/crawled/closed_tickets.json"
PREPROCESSED_PATH = "data/dynamic/tickets/closed_tickets.json"
BACKUP_DIR = r"G:\My Drive\DBBackup\ai-crew"

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
            ticket.get("full_thread_summary", ""),  # Note: typo preserved from original code "sumary"
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
    
    # Step 1: Preprocess tickets
    if not run_preprocessing():
        print("❌ Preprocessing failed. Database insertion skipped.")
        return
    
    # Step 2: Load preprocessed tickets
    if not os.path.exists(PREPROCESSED_PATH):
        print(f"❌ Preprocessed JSON file not found: {PREPROCESSED_PATH}")
        return
        
    tickets = load_tickets_from_json(PREPROCESSED_PATH)
    
    # Step 3: Insert tickets into database
    insert_into_db(tickets, DB_PATH)
    
    # Step 4: Backup the database
    if backup_database(DB_PATH, BACKUP_DIR):
        print("✅ Database backup completed successfully!")
    else:
        print("⚠️ Process completed but database backup failed.")
        
    print("✅ Combined process completed successfully!")

if __name__ == "__main__":
    main()
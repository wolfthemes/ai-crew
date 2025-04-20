
import sqlite3
import json
import os

DB_PATH = "data/db/closed_tickets.db"
JSON_PATH = "data/dynamic/tickets/closed_tickets.json"

def load_tickets_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)["closed_tickets"]

def ensure_tables(cursor):
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
            ticket.get("full_thread_sumary", ""),
            ticket.get("time_stamp", "")
        ))
    conn.commit()
    conn.close()

def main():
    if not os.path.exists(JSON_PATH):
        print(f"❌ JSON file not found: {JSON_PATH}")
        return
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    tickets = load_tickets_from_json(JSON_PATH)
    insert_into_db(tickets, DB_PATH)
    print(f"✅ Inserted {len(tickets)} tickets into {DB_PATH}")

if __name__ == "__main__":
    main()

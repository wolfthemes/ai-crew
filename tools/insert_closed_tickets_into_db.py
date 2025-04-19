import json
import sys
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Load JSON
with open("data/dynamic/tickets/closed_tickets.json", "r") as f:
    data = json.load(f)

# Connect to SQLite DB
conn = sqlite3.connect("data/db/closed_tickets.db")
cursor = conn.cursor()

# Loop through tickets and insert
for ticket in data["closed_tickets"]:
    cursor.execute("""
        INSERT OR REPLACE INTO closed_tickets (
            id, subject, customer, theme, builder, version, updated,
            category, ticket_url, first_message, last_message, formatted_text_thread,
            last_message_timestamp, last_message_summary, full_thread_sumary,
            contains_credentials, match_source, ai_reply, needs_human
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket["id"],
        ticket["subject"],
        ticket["customer"],
        ticket["theme"],
        ticket["builder"],
        ticket["version"],
        ticket["updated"],
        ticket.get("category", ""),
        ticket["ticket_url"],
        ticket["first_message"],
        ticket["last_message"],
        ticket["formatted_text_thread"],
        ticket["last_message_timestamp"],
        ticket["last_message_summary"],
        ticket["full_thread_sumary"],
        ticket["contains_credentials"],
        ticket["match_source"],
        ticket["ai_reply"],
        ticket["needs_human"]
    ))

conn.commit()
conn.close()

import sqlite3

def fetch_closed_tickets(db_path="data/db/closed_tickets.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM closed_tickets;")
    rows = cursor.fetchall()

    print(f"Found {len(rows)} closed tickets:\\n")
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    fetch_closed_tickets()
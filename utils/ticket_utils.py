# utils/ticket_utils.py
import json
from html import unescape

import json

def load_ticket(filepath="data/open_tickets.json", index=0):
    """
    Load a single ticket from the JSON file.
    
    Args:
        filepath (str): Path to the JSON file with ticket data.
        index (int): Index of the ticket to load (default: 0).
        
    Returns:
        dict: Ticket data for the specified ticket.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    
    tickets = data.get("open-tickets", [])
    if index < len(tickets):
        return tickets[index]
    else:
        raise IndexError(f"No ticket at index {index}.")

def extract_latest_user_comment(comments):
    """Return the first user comment from the comments list, unescaped and formatted."""
    user_comments = [c for c in comments if c.get('user_type') == 'user']
    if user_comments:
        return unescape(user_comments[0].get('comment', '').replace('\\n', '\n'))
    return ""

def should_process_ticket(ticket):
    """Only process ticket if it needs a response."""
    return ticket.get("needs_response") == "1"

def format_ticket_history(comments, max_entries=50):
    visible = [c for c in comments if c['private'] == "0"]
    latest = visible[-max_entries:]
    history = []
    for c in latest:
        name = c['commenter_name']
        role = "User" if c['user_type'] == 'user' else "Support"
        msg = unescape(c['comment'].replace('\n', '\n'))
        history.append(f"[{role}] {name}:\n{msg}\n")
    return "\n".join(history)

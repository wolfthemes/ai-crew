# utils/ticket_utils.py
import json
from html import unescape

def load_ticket(ticket_path):
    with open(ticket_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["open-tickets"][0]  # or loop over entries if batch processing

def extract_latest_user_comment(comments):
    user_comments = [c for c in comments if c['user_type'] == 'user']
    if user_comments:
        return unescape(user_comments[-1]['comment'].replace('\n', '\n'))
    return ""

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

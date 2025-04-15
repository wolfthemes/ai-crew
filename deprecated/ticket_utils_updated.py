
import re
import json
from html import unescape
from pathlib import Path

def contains_credentials(text):
    """Detect if the comment includes login credentials."""
    patterns = [
        r"wp-admin", r"username[:\s]", r"password[:\s]",
        r"login[:\s]", r"ftp", r"site access", r"admin login"
    ]
    text = text.lower()
    return any(re.search(p, text) for p in patterns)

def extract_latest_user_comment(comments):
    user_comments = [c for c in comments if c.get('user_type') == 'user']
    if user_comments:
        return unescape(user_comments[-1].get('comment', '').replace('\\n', '\n'))
    return ""

def format_ticket_history(comments, max_entries=50):
    visible = [c for c in comments if c.get('private') == "0"]
    latest = visible[-max_entries:]
    history = []
    for c in latest:
        name = c['commenter_name']
        role = "User" if c['user_type'] == 'user' else "Support"
        msg = unescape(c['comment'].replace('\n', '\n'))
        history.append(f"[{role}] {name}:\n{msg}\n")
    return history

def extract_theme_from_envato(envato_verified_string):
    try:
        envato_data = json.loads(envato_verified_string)
        item_name = envato_data.get("item_name", "")
        theme_name = item_name.split("-")[0].strip()
        return theme_name
    except Exception:
        return "Unknown"

def preprocess_ticket(raw_ticket, theme_metadata, classify_ticket_func):
    comments = raw_ticket["ticket_comments"]
    first_msg = unescape(comments[0]["comment"])
    last_msg = extract_latest_user_comment(comments)
    full_thread = format_ticket_history(comments)

    theme = extract_theme_from_envato(raw_ticket.get("envato_verified_string", "{}"))
    builder = theme_metadata.get(theme, {}).get("builder", "Unknown")

    user_site = raw_ticket.get("related_url", "—")
    customer_name = raw_ticket.get("user_name", "Unknown")
    customer_url = f"https://wolfthemes.ticksy.com/user/{raw_ticket.get('user_id')}"
    ticket_url = f"https://wolfthemes.ticksy.com/ticket/{raw_ticket['ticket_id']}"

    match_source = classify_ticket_func(last_msg)
    needs_human = contains_credentials(last_msg)

    return {
        "id": raw_ticket["ticket_id"],
        "subject": raw_ticket["ticket_title"],
        "customer": customer_name,
        "customer_url": customer_url,
        "theme": theme,
        "builder": builder,
        "user_site": user_site,
        "ticket_url": ticket_url,
        "first_message": first_msg,
        "last_message": last_msg,
        "full_thread": full_thread,
        "summary": last_msg[:120] + "…" if len(last_msg) > 120 else last_msg,
        "match_source": match_source,
        "ai_reply": "",
        "needs_human": needs_human
    }

def preprocess_all_tickets(filepath, theme_metadata, classify_ticket_func):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    for t in data.get("open-tickets", []):
        if t.get("needs_response") == "1":
            processed.append(preprocess_ticket(t, theme_metadata, classify_ticket_func))
    return processed

def save_preprocessed_tickets(tickets, output_path="data/preprocessed_tickets.json"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"preprocessed_tickets": tickets}, f, indent=2, ensure_ascii=False)

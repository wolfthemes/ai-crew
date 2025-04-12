# utils/ticket_utils.py
import os
import re
import json
from openai import OpenAI
from html import unescape
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
#openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_ticket(comments: list[str]) -> str:
    """Summarize the latest user message into one clean sentence."""
    if not comments:
        return "No summary available."

    full_text = "\n\n".join(comments)
    prompt = (
        "Summarize the core issue from this support ticket in a very short, label-style sentence. "
        "Do not include the user's name, and do not start with phrases like 'The user is experiencing' or 'The issue is'. "
        "Use 5 to 10 words max, focusing only on the main problem:\n\n"
        f"{full_text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a support assistant summarizing support tickets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ OpenAI summarization failed: {e}")
        return "Summary generation failed."

def contains_credentials(text):
    """Detect if the comment includes login credentials."""
    patterns = [
        r"wp-admin", r"username[:\s]", r"password[:\s]",
        r"login[:\s]", r"ftp", r"site access", r"admin login"
    ]
    text = text.lower()
    return any(re.search(p, text) for p in patterns)

def load_ticket(filepath="data/crawled/open_tickets.json", index=0):
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

def extract_latest_user_comment_timestamp(comments):
    user_comments = [c for c in comments if c.get('user_type') == 'user']
    if user_comments:
        return unescape(user_comments[0].get('time_stamp', '').replace('\\n', '\n'))
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
    last_msg_timestamp = extract_latest_user_comment_timestamp(comments)
    full_thread = format_ticket_history(comments)

    theme = extract_theme_from_envato(raw_ticket.get("envato_verified_string", "{}"))
    builder = theme_metadata.get(theme, {}).get("builder", "Unknown")

    summary = summarize_ticket(full_thread)
    #summary = "Tickets summary in once clear sentence"

    user_site = raw_ticket.get("related_url", "—")
    customer_name = raw_ticket.get("user_name", "Unknown")
    customer_url = f"https://ticksy.com/user/{raw_ticket.get('user_id')}"
    ticket_url = f"https://ticksy.com/ticket/{raw_ticket['ticket_id']}"

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
        "last_message_timestamp": last_msg_timestamp,
        "full_thread": comments,
        "formatted_text_thread": full_thread,
        "summary": summary,
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

def save_preprocessed_tickets(tickets, output_path="data/dynamic/preprocessed_tickets.json"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"preprocessed_tickets": tickets}, f, indent=2, ensure_ascii=False)

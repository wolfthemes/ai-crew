# utils/ticket_utils.py
import os
import re
import json
from openai import OpenAI
from html import unescape
from pathlib import Path
from dotenv import load_dotenv
from utils.ticket_classifier import classify_ticket
from tools.vector_retriever import reformulate_agent_instructions_text

load_dotenv()

openai_client = OpenAI()
#openai.api_key = os.getenv("OPENAI_API_KEY")

def reformulate_reply(reply_text: str, instruction: str = "", last_user_message: str = "") -> str:
    """
    Reformulates the AI reply with optional extra instruction and original customer message for context.
    Preserves formatting, tone, and details.
    """
    from llm_config_local import SECONDARY_MODEL_KEY

    openai_client = OpenAI()

    system_prompt = reformulate_agent_instructions_text

    user_prompt = f"""Customer message:
    {last_user_message.strip()}

    Instruction:
    {instruction.strip()}

    Reply to reformulate (in HTML):
    {reply_text.strip()}
    """

    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4
    )

    #print( response.choices[0].message.content.strip() )

    return response.choices[0].message.content.strip()


def summarize_ticket(comments: list[str]) -> str:
    """Summarize the ticket thread into one clean sentence."""
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
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
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
    
def summarize_last_user_comment(comments: list[str], last_msg: str) -> str:
    """Summarize the last user comment from this ticket thread into one clean sentence."""
    
    if not comments:
        return "No summary available."

    full_text = "\n\n".join(comments)
    
    prompt = (
        "You are a support assistant summarizing a customer request.\n\n"
        "Below is the full support thread for context, followed by the last user message.\n"
        "Your task is to summarize the **last user message** as a very short, label-style sentence.\n\n"
        "⚠️ Do NOT include the user's name.\n"
        "⚠️ Do NOT start with phrases like 'The user is experiencing...'\n"
        "✅ Make it short (5 to 10 words max) and specific:\n\n"
        "---\n"
        f"Full thread:\n{full_text}\n\n"
        "---\n"
        f"Last user message:\n{last_msg}\n\n"
        "Summary:"
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-nano",
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


def extract_first_user_comment(comments):
    """Return the last user comment from the comments list, unescaped and formatted."""
    user_comments = [c for c in comments if c.get('user_type') == 'user']
    if user_comments:
        return unescape(user_comments[0].get('comment', '').replace('\\n', '\n'))
    return ""

def extract_latest_user_comment(comments):
    """Return the first user comment from the comments list, unescaped and formatted."""
    user_comments = [c for c in comments if c.get('user_type') == 'user']
    if user_comments:
        return unescape(user_comments[-1].get('comment', '').replace('\\n', '\n'))
    return ""

def extract_latest_user_comment_timestamp(comments):
    user_comments = [c for c in comments if c.get('user_type') == 'user']
    if user_comments:
        return unescape(user_comments[-1].get('time_stamp', '').replace('\\n', '\n'))
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

def preprocess_ticket(raw_ticket):
    TICKSY_DOMAIN = os.getenv("TICKSY_DOMAIN")

    # Tickets info
    comments = list(reversed(raw_ticket["ticket_comments"])) # order is reversed from ticksy crawled data
    first_msg = extract_first_user_comment(comments)
    last_msg = extract_latest_user_comment(comments)
    last_msg_timestamp = extract_latest_user_comment_timestamp(comments)
    full_thread = format_ticket_history(comments)
    full_thread_summary = summarize_ticket(full_thread)
    last_msg_summary = summarize_last_user_comment(full_thread,last_msg)
    ticket_type = raw_ticket["ticket_type"]

    # Theme info
    theme = extract_theme_from_envato(raw_ticket.get("envato_verified_string", "{}"))
    theme_url = get_theme_url(theme)
    theme_demo_url = get_theme_demo_url(theme)
    builder = get_theme_builder(theme)
    category = get_theme_category(theme)
    version = get_theme_version(theme)
    last_update = get_theme_last_update(theme)
    envato_id = get_theme_envato_id(theme)
    
    #summary = "Tickets summary in once clear sentence"
    # User info
    user_site = raw_ticket.get("related_url", "—")
    customer_name = raw_ticket.get("user_name", "Unknown")
    customer_url = f"https://{TICKSY_DOMAIN}.ticksy.com/customer/{raw_ticket.get('user_id')}"
    ticket_url = f"https://{TICKSY_DOMAIN}.ticksy.com/ticket/{raw_ticket['ticket_id']}"

    match_source = classify_ticket(full_thread)
    contains_credentials_value = contains_credentials(full_thread)
    needs_human = "false"

    return {
        "id": raw_ticket["ticket_id"],
        "time_stamp": raw_ticket["time_stamp"],
        "subject": raw_ticket["ticket_title"],
        "customer": customer_name,
        "customer_url": customer_url,
        "theme": theme,
        "builder": builder,
        "category": category,
        "version": version,
        "updated": last_update,
        "envato_id": envato_id,
        "theme_url": theme_url,
        "theme_demo_url": theme_demo_url,
        "user_site": user_site,
        "ticket_url": ticket_url,
        "ticket_type" : ticket_type,
        "first_message": first_msg,
        "last_message": last_msg,
        "last_message_timestamp": last_msg_timestamp,
        "last_message_summary": last_msg_summary,
        "full_thread_summary": full_thread_summary,
        "formatted_text_thread": full_thread,
        "contains_credentials" : contains_credentials_value,
        "match_source": match_source,
        "ai_reply": "",
        "needs_human": needs_human,
        "full_thread": comments,
    }

def get_theme_url(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['url']
    
    return f"Unknown"

def get_theme_envato_id(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['itemId']
    
    return f"Unknown"

def get_theme_demo_url(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['demourl']
    
    return f"Unknown"

def get_theme_builder(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['builder']
    
    return f"Unknown"
    
def get_theme_category(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['category']
    
    return f"Uncategorized"

def get_theme_last_update(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['updated']
    
    return f"No date available"
    
def get_theme_version(theme_name):
    with open(os.path.join("data", "themes/theme_catalog.json"), encoding="utf-8") as f:
        data = json.load(f)
    
    # Loop through all themes to match by name
    for theme in data.values():
        if theme.get("name", "").lower() == theme_name.lower():
            return theme['version']
    
    return f"No version found"

def get_ticket_metadata(ticket_id):
    ticket = load_ticket_by_id(ticket_id)
    
    if not ticket:
        return {}
    

    # TODO: strip attachements from comments

    return {
        "ticket_id": ticket_id,
        "timestamp": ticket.get("timestamp"),
        "ticket_type": ticket.get("ticket_type"),
        "user_site": ticket.get("user_site"),
        "subject": ticket.get("subject"),
        "customer": ticket.get("customer"),
        "customer_url": ticket.get("customer_url"),
        "theme": ticket.get("theme"),
        "builder": ticket.get("builder"),
        "category": ticket.get("category"),
        "version": ticket.get("version"),
        "theme_url": ticket.get("theme_url"),
        "theme_demo_url": ticket.get("theme_demo_url"),
        "envato_id": ticket.get("envato_id"),
        "updated": ticket.get("updated"),
        "user_site": ticket.get("user_site"),
        "ticket_url": ticket.get("ticket_url"),
        "first_message": ticket.get("first_message"),
        "last_message": ticket.get("last_message"),
        "last_message_timestamp": ticket.get("last_message_timestamp"),
        "last_message_summary": ticket.get("last_message_summary"),
        "full_thread_summary": ticket.get("full_thread_summary"),
        "formatted_text_thread": ticket.get("formatted_text_thread"),
        "contains_credentials" : ticket.get("contains_credentials"),
        "match_source": ticket.get("match_source"),
        "ai_reply": "",
        "full_thread": ticket.get("full_thread"),
        "flags": {
            "needs_human": ticket.get("needs_human", False),
            "private": ticket.get("private", False)
        }
    }

def preprocess_open_tickets(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    for t in data.get("open-tickets", []):
        if t.get("needs_response") == "1":
            processed.append(preprocess_ticket(t))
    return processed

def preprocess_closed_tickets(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    for t in data.get("closed-tickets", []):
        # Skip invalid or unhelpful tickets (non-theme-cateogry, deleted customer )
        if t.get("user_name") == "[deleted]" or t.get("category_id") == "100010795":
            continue
        processed.append(preprocess_ticket(t))

    return processed

def save_preprocessed_open_tickets(tickets, output_path="data/dynamic/tickets/open_tickets.json"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"open_tickets": tickets}, f, indent=2, ensure_ascii=False)

def save_preprocessed_closed_tickets(tickets, output_path="data/dynamic/tickets/closed_tickets.json"):
    # TODO dump in DB instead
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"closed_tickets": tickets}, f, indent=2, ensure_ascii=False)

def load_ticket_by_id(ticket_id, path="data/dynamic/tickets/open_tickets.json"):
    """
    Load a specific ticket by ID from the preprocessed tickets file.

    Args:
        ticket_id (int or str): The ID of the ticket to load.
        path (str): Path to the preprocessed ticket data file.

    Returns:
        dict or None: The ticket data dict if found, otherwise None.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            tickets = all_data.get("open_tickets", [])
            for ticket in tickets:
                if str(ticket["id"]) == str(ticket_id):
                    return ticket
    except Exception as e:
        print(f"Error loading ticket by ID {ticket_id}: {e}")
    
    return None

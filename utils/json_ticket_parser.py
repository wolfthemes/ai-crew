# utils/json_ticket_parser.py

import json
import html
from utils.ticket_utils import extract_latest_user_comment, format_ticket_history

def parse_json_ticket(ticket: dict) -> dict:
    # Load theme name from the JSON string in 'envato_verified_string'
    theme_info = {}
    try:
        theme_info = json.loads(ticket.get("envato_verified_string", "{}"))
    except json.JSONDecodeError:
        pass

    return {
        "ticket_id": ticket.get("ticket_id"),
        "customer_name": ticket.get("user_name") or ticket.get("user_email"),
        "theme": theme_info.get("item_name", "Unknown Theme"),
        "url": ticket.get("related_url", None),
        "latest_user_comment": extract_latest_user_comment(ticket["ticket_comments"]),
        "history": format_ticket_history(ticket["ticket_comments"], max_entries=50),
        "raw": ticket,
    }

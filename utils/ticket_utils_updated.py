
def extract_latest_user_comment(comments):
    """Return the first comment authored by the user."""
    for c in comments:
        if c.get("author", "").lower() == "user":
            return c.get("comment", "").strip()
    return None

def should_process_ticket(ticket):
    """Only process ticket if it needs a response."""
    return ticket.get("needs_response") == "1"

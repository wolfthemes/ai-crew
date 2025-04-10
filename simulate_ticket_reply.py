import json
from crewai import Task
from agents.support_agent import support_agent
from utils.ticket_utils import load_ticket, extract_latest_user_comment, format_ticket_history

ticket_data = load_ticket('data/open_tickets.json')  # Assuming you have a function that returns this dict

# 1. Format history (e.g., 5 last comments)
history_text = format_ticket_history(ticket_data["ticket_comments"], max_entries=5)

# 2. Extract the latest question for reply
latest_comment = extract_latest_user_comment(ticket_data["ticket_comments"])

support_task = Task(
    description=f"""
You are responding to an ongoing support ticket.

Customer: {ticket_data['user_name']}
Theme: {json.loads(ticket_data['envato_verified_string'])['item_name']}
URL: {ticket_data['related_url']}

Latest message from the user:
"{latest_comment}"

--- Conversation history (most recent last) ---
{history_text}

---

Use all available context and keep the reply focused.
""",
    expected_output="Markdown formatted reply that fits into the ongoing conversation naturally.",
    agent=support_agent,
)

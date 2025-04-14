from crewai import Task
from crewai import Crew
from agents.support_agent import support_agent
from utils.ticket_utils import load_ticket, extract_latest_user_comment, format_ticket_history, should_process_ticket
from utils.ticket_classifier import classify_ticket

from utils.document_loaders import load_guidelines

guidelines = load_guidelines()
ticket = load_ticket(index=0)

if not should_process_ticket(ticket):
    print("🚫 Skipping — this ticket doesn't need a response.")
    exit()

user_comment = extract_latest_user_comment(ticket["ticket_comments"])
history_text = format_ticket_history(ticket["ticket_comments"], max_entries=50)
category = classify_ticket(user_comment)

support_task_conversation = Task(
    description=f"""
You are responding to this ongoing customer support ticket.

Theme: {ticket['envato_verified_string']}
Related URL: {ticket.get('related_url')}

### Ticket history:
{history_text}

---

### Latest user message:
"{user_comment}"

Classify the issue and respond as accurately as possible using the knowledge base and support rules.

{guidelines}

Use markdown formatting and be concise and helpful.
""",
    expected_output="Markdown formatted support reply that directly addresses the customer's issue.",
    agent=support_agent,
)

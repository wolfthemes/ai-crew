# run_json_ticket.py
import json
from utils.json_ticket_parser import parse_json_ticket
from crews.support_crew import support_crew_with_research

def run_ticket_task_from_json(parsed_ticket: dict) -> str:
    # Format a plain text version that mimics Streamlit drop input
    simulated_input = f"""
Customer: {parsed_ticket['customer_name']}
Theme: {parsed_ticket['theme']}
URL: {parsed_ticket['url'] or 'N/A'}

### Ticket History
{parsed_ticket['history']}

---

### Latest User Message
{parsed_ticket['latest_user_comment']}
""".strip()

    # Run the crew on that "text version"
    return support_crew_with_research(simulated_input)

with open("data/crawled/open_tickets.json", encoding="utf-8") as f:
    tickets = json.load(f)["open-tickets"]

# Pick the first ticket just for test
ticket_data = parse_json_ticket(tickets[0])
reply = run_ticket_task_from_json(ticket_data)

print("Suggested reply:\n", reply)

from crewai import Task
from agents.support_agent import support_agent

ticket_text = """
Ticket from user:

"Hello, I just installed the Phase theme, but the Elementor artist slider doesn't display any content.
I tried clearing cache and deactivating plugins but it’s still not working."
"""

support_task = Task(
    description=f"""
You're responding to a real customer support ticket.
Do NOT summarize or restate the user’s message. 
Do NOT use generic lines like 'thank you for contacting us'. 
Just give the clearest, most relevant answer — like a human expert would.

Here is the ticket:
{ticket_text}
""",
    expected_output="Markdown reply for Ticksy.",
    agent=support_agent,
)


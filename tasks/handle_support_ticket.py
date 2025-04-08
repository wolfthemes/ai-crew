from crewai import Task
from agents.support_agent import support_agent

ticket_text = """
Ticket from user:

"Hi, I’m getting an error that says ‘The package could not be installed. The theme is missing the style.css stylesheet.’ when I try to upload the theme on WordPress."
"""

support_task = Task(
    description=f"""
You're responding to a real customer support ticket.
Do NOT summarize or restate the user’s message. 
Do NOT use generic lines like 'thank you for contacting us'. 

Just give the clearest, most relevant answer — like a human expert would.
Use the knowledge base loaded in your memory if applicable.

Here is the ticket:
{ticket_text}
""",
    expected_output="Markdown reply for Ticksy.",
    agent=support_agent,
)


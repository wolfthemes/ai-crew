from crewai import Task
from agents.support_agent import support_agent
from utils.ticket_classifier import classify_ticket, split_ticket_into_parts
from utils.document_loaders import load_guidelines

guidelines = load_guidelines()

# I have a few issues:

# How to update WPBakery to 8.3.1.? 
# I can't activate Slider Revolution?

# Also, when I import the demo I have an error..

# I noticed that my admin is slow after activating the theme.

# Lastly is it possible to add a Jiggily Biggily plugin compatiblity?
# I would like to cusomtize the appearance of the shop with this.

ticket_text = """
Ticket from user:

"How to update WPBakery to 8.3.1.? I'm using Herion theme"
"""

parts = split_ticket_into_parts(ticket_text)
classified_parts = [(p, classify_ticket(p)) for p in parts]

issue_summary = "\\n".join([f"- {cat}: \"{part}\"" for part, cat in classified_parts])

support_task_fresh = Task(
    description=f"""
    You are responding to this customer support ticket:

   {ticket_text}

   {guidelines}

   ---

    Internally, this ticket contains the following parts:
   {issue_summary}

   Respond to each in the most accurate way possible.
    """,
    expected_output="Markdown formatted support reply that directly addresses the customer's issue.",
    agent=support_agent,
)


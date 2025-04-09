from crewai import Task
from agents.support_agent import support_agent

#I am fixing an old site with Speaker Version: 1.0.2.5, I want to update the newest version. Do I need to purchase it again?

ticket_text = """
Ticket from user:

"Why does my social media icons are not working on this theme? How can I fix it?"
"""

support_task = Task(
    description=f"""
    You are responding to this customer support ticket:

    {ticket_text}

    Follow these guidelines when creating your response:
    
    1. GREETING:
       - If customer's name is clearly identifiable (e.g., John, Roberto, Maria), start with "Hi [name],"
       - Otherwise, start with "Hi there,"
    
    2. ISSUE CATEGORIZATION:
       - First, determine if this is: a common issue, an actual bug, requires more information, or is a customization/installation request
       - Include your categorization in your internal reasoning, but DON'T state it explicitly to the customer
    
    3. RESPONSE APPROACH:
       - For common issues: Provide the solution with a link to relevant knowledge base article if available
       - For bugs: Acknowledge the issue and provide troubleshooting steps or timeline for fix
       - For information gaps: Clearly request the specific details needed (screenshots, URL, admin access)
       - For customization/installation: Politely explain this is beyond standard support and link to https://wolfthemes.com/services
    
    4. STYLE GUIDELINES:
       - Be professional but warm
       - Keep responses concise and action-oriented
       - Use markdown formatting for clarity (bold for important points, code blocks for code)
       - Don't use generic phrases like "thank you for contacting us" or "hope this helps"
       - Don't summarize or restate the customer's issue
    
    5. SIGNATURE:
       - End with "WolfThemes Support"
    """,
    expected_output="Markdown formatted support reply that directly addresses the customer's issue.",
    agent=support_agent,
)


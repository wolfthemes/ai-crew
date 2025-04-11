from crewai import Task
from agents.research_agent import research_agent

def create_research_task(ticket_text: str) -> Task:
    return Task(
        description=f"""
        Parse the following support ticket and extract the following:
        - Customer name (if signed)
        - Theme name or slug (guess if not clear)
        - Website URL (if any)
        - All distinct issues or parts (split logically)

        For each part, use the knowledge base to find an existing solution if available.
        If the match is a STRICT_RESPONSE, include it.

        Return a structured JSON list like:
        [
          {{
            "part": "How to update WPBakery with Herion?",
            "match": {{
              "source": "common_issue",
              "title": "...",
              "content": "STRICT_RESPONSE: ..."
            }}
          }},
          ...
        ]
        
        Ticket:
        {ticket_text}
        """,
        expected_output="Structured list of ticket parts with matched KB entries.",
        agent=research_agent,
    )

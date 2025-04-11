from crewai import Task
from agents.research_agent import research_agent

def create_research_task(ticket_data: dict) -> Task:
    return Task(
        description=f"""Analyze the following support ticket and:
        - Identify all distinct issues
        - For each issue:
            1. Detect related theme
            2. Retrieve solution from resources in this strict order:
               common_issues → kb_articles → theme_note → theme_doc → support_ticket
        - Return a list of issues with:
          {{
            "issue_summary": "...",
            "matched_source": "...",
            "content_used": "...",
            "theme": "..."
          }}
        
        Ticket:
        {ticket_data}
        """,
        agent=research_agent,
        expected_output="A structured list of issues with matched sources and extracted content."
    )

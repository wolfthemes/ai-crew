from crewai import Task
from agents.research_agent import research_agent

def create_research_task(ticket_text: str) -> Task:
    return Task(
        description=f"""
        You must do only one thing:

        🔍 Search for a STRICT_RESPONSE match to this ticket using the knowledge base.
        You can only use entries marked as `common_issue`.

        If a match is found:
        - Return only the STRICT_RESPONSE content exactly as it is (no editing).
        - Use this structure:

        STRICT_RESPONSE:
        <full content here>

        If no STRICT_RESPONSE is found:
        - Return only: NO_MATCH

        Ticket:
        {ticket_text}
        """,
        expected_output="Structured list of ticket parts with matched KB entries.",
        agent=research_agent,
    )

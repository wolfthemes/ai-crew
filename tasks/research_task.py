from crewai import Task
from core.research_processor import process_ticket_research
from agents.research_agent import research_agent

def create_research_task(ticket_text: str) -> Task:
    research_output = process_ticket_research(ticket_text)

    task = Task(
        description="Pre-parsed ticket. Research has been done already.",
        expected_output="Structured ticket parts and KB matches.",
        agent=research_agent
    )

    # Here we fake the task having already run and returned the result
    task._output = {
        "research_output": research_output
    }

    return task

from crewai import Crew
from tasks.task_fresh_ticket import support_task_fresh
from tasks.task_ticket_followup import support_task_conversation
from agents.support_agent import support_agent

support_crew_fresh = Crew(
    agents=[support_agent],
    tasks=[support_task_fresh],
    verbose=True
)

support_crew_conversation = Crew(
    agents=[support_agent],
    tasks=[support_task_conversation],
    verbose=True
)
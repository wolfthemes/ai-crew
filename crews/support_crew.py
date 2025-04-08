from crewai import Crew
from tasks.handle_support_ticket import support_task
from agents.support_agent import support_agent

support_crew = Crew(
    agents=[support_agent],
    tasks=[support_task],
    verbose=True
)
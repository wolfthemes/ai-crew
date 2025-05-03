from crewai import Crew, Process
from agents.dev.dev_agent import dev_agent

def dev_crew(task = dict):
    return Crew(
        agents=[dev_agent],
        tasks=[task],
    )
    
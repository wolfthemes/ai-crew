from crewai import Crew, Task
from agents.dev_agent import dev_agent

while True:
    query = input("Ask Dev Agent: ")
    if query.lower() in ["exit", "quit"]:
        break

    task = Task(description=query, agent=dev_agent)
    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()
    print("\nResult:\n", result)

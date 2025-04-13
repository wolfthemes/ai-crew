from crewai import Crew, Task
from agents.dev_agent import dev_agent
import json

while True:
    query = input("\nAsk Dev Agent (or type JSON for structured tool input):\n> ")
    if query.lower() in ["exit", "quit"]:
        break

    try:
        # Try parsing as JSON for tool input
        user_input = json.loads(query)
        task = Task(
            description="Dev task using structured input.",
            agent=dev_agent,
            input=user_input,
            expected_output="Exact file and line of the matching function in the repo."
        )
    except json.JSONDecodeError:
        # Natural language input
        task = Task(
            description=query,
            agent=dev_agent,
            expected_output="A concise and actionable response to the developer question."
        )

    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()
    print("\nResult:\n", result)

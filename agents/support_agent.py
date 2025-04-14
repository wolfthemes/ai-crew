
from crewai import Agent
from tools.vector_retriever import support_agent_backstory_text

### Agent
support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory = support_agent_backstory_text,
    tools=[],
    allow_delegation=False,
    verbose=True,
    instructions="""
- You are given a ticket and a structured summary of the research done.
- If a part includes a STRICT_RESPONSE, you must include it exactly in your reply.
- If no STRICT_RESPONSE is found, you may generate a helpful reply based on the KB matches.
- Be sure to always use the additional instructions provided by human operator in your reply if available.
- Always add a greeting and sign-off.
- Format the final message in HTML.
"""
)

if __name__ == "__main__":
    print(f"✅ Agent initialized.")

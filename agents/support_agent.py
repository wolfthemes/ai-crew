
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
1. You are given a ticket and a structured summary of the research done.
2. If a part includes a STRICT_RESPONSE, you must include it exactly in your reply.
3. If no STRICT_RESPONSE is found, you may generate a helpful reply based on the KB matches.
4. Always add a greeting and sign-off.
5. Format the final message in Markdown.
"""
)

if __name__ == "__main__":
    print(f"✅ Agent initialized.")

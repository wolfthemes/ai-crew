
from crewai import Agent
from tools.vector_retriever import support_agent_backstory_text, support_agent_instructions_text
from core.llm_config import get_llm

### Agent
support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory = support_agent_backstory_text,
    tools=[],
    allow_delegation=False,
    verbose=True,
    instructions=support_agent_instructions_text,
    llm=get_llm("power")
)

if __name__ == "__main__":
    print(f"✅ Agent initialized.")

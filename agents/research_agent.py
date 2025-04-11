from crewai import Agent
from tools.kb_search_tool import KBSearchTool

research_agent = Agent(
    role="Support Researcher",
    goal="Extract user issues from support ticket and find solutions from the knowledge base with strict priority",
    backstory="You're an assistant who specializes in identifying support problems and finding exact solutions using a strict source order.",
    tools=[KBSearchTool()],
    verbose=True
)
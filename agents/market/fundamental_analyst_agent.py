from crewai import Agent
from core.llm_config import get_llm

fundamental_analyst_agent = Agent(
    role="Fundamental Analyst Agent",
    goal="Provide fundamental analysis of euro and dollar drivers",
    #tools=[WebSearchTool()],
    backstory="A macroeconomist with deep knowledge of global markets."
)
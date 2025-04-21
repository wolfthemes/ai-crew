from crewai import Agent
from core.llm_config import get_llm

economic_news_agent = Agent(
    role="Economic News Agent",
    goal="Collect and summarize economic events for the upcoming week impacting EUR/USD",
    #tools=[SerpAPIWrapper()],
    backstory="A meticulous researcher skilled at identifying high-impact economic events."
)
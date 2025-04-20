from crewai import Agent
from tools.notion_writer import PostToNotion
from tools.fxstreet_scraper import FetchFXNews

market_analyst_agent = Agent(
    role="EUR/USD Market Analyst",
    goal="Summarize EUR/USD market news into a daily report",
    backstory="You are a macro-focused financial analyst with a clear and actionable writing style.",
    tools=[FetchFXNews(), PostToNotion()],
    allow_delegation=False
)

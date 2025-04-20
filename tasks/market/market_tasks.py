from crewai import Task
from agents.market.market_analyst_agent import market_analyst_agent

daily_market_task = Task(
    description=(
        "Analyze current EUR/USD headlines and synthesize a daily market brief "
        "including key headlines, sentiment, analyst notes, and upcoming events. "
        "Format the output in Markdown for Notion."
    ),
    expected_output="A concise daily EUR/USD market report in Markdown format",
    agent=market_analyst_agent
)

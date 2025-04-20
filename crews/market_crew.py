from crewai import Crew
from agents.market.market_analyst_agent import market_analyst_agent
from tasks.market.market_tasks import daily_market_task

market_crew = Crew(
    agents=[market_analyst_agent],
    tasks=[daily_market_task],
    verbose=True
)

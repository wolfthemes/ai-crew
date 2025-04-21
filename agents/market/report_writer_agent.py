from crewai import Agent
from core.llm_config import get_llm

report_writer_agent = Agent(
    role="Report Writer Agent",
    goal="Compile a structured EUR/USD market analysis report",
    tools=[],
    backstory="A skilled financial writer adept at synthesizing data."
)
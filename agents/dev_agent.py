from crewai import Agent
from tools.github_tools import create_pr
from tools.code_search_tools import search_function

dev_agent = Agent(
    role="Dev Agent",
    goal="Help with WordPress plugin development tasks",
    tools=[],
    backstory="A helpful developer that understands PHP and WordPress codebases.",
    verbose=True
)
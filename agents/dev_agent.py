from crewai import Agent
from tools.code_search_tools import GetCodeSearchTool
from tools.github_tools import GitHubTool

dev_agent = Agent(
    role="Dev Agent",
    goal="Help with WordPress plugin development tasks",
    tools=[GetCodeSearchTool(),GitHubTool()],
    backstory="A helpful developer that understands PHP and WordPress codebases.",
    verbose=True
)
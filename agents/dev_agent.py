from crewai import Agent
from tools.code_search_tools import GetCodeSearchTool
from tools.github_tools import GitHubTool
from tools.fix_code_tool import FixCodeTool

dev_agent = Agent(
    role="Dev Agent",
    goal="Help with WordPress themes and plugin development tasks",
    tools=[GetCodeSearchTool(),GitHubTool(),FixCodeTool()],
    backstory="A helpful expert developer that understands PHP, JS, CSS and WordPress codebases.",
    verbose=True
)
from crewai import Agent
from tools.vector_retriever import dev_agent_backstory_text
from tools.code_search_tools import GetCodeSearchTool
from tools.github_tools import GitHubTool
from tools.fix_code_tool import FixCodeTool
from tools.file_operations_tool import FileOperationsTool
from tools.wp_toolkit import WordPressToolkit
from tools.git_operations_tool import GitOperationsTool

dev_agent = Agent(
    role="Dev Agent",
    goal="Help with WordPress themes and plugin development tasks",
    tools=[
        GetCodeSearchTool(),
        GitHubTool(),
        FixCodeTool(),
        FileOperationsTool(),
        WordPressToolkit(),
        GitOperationsTool()
    ],
    backstory=dev_agent_backstory_text,
    verbose=True,
    llm="gpt-4"
)
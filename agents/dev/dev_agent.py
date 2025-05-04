from crewai import Agent
from core.llm_config import get_llm
from tools.git.github_operations_tool import GitHubTool, GitOperationsTool

from tools.code_operations.code_search_tools import CodeSearchTool  
from tools.code_operations.fix_code_tool import FixCodeTool
from tools.code_operations.patch_tool import PatchTool
from tools.code_operations.ast_parser_tool import ASTParserTool
from tools.code_operations.code_snippet_tool import CodeSnippetTool
from tools.code_operations.code_occurrence_counter import CodeOccurrenceCounter

from tools.file_operations.file_content_tool import FileContentTool
from tools.file_operations.file_operations_tool import FileOperationsTool

from tools.wp_operations.wp_toolkit import WordPressToolkit
from tools.wp_operations.wp_function_finder_tool import WordPressFunctionFinderTool

from utils.document_loaders import load_dev_agent_backstory

dev_agent_backstory_text = load_dev_agent_backstory()

# Create the enhanced dev agent with all tools organized by category
dev_agent = Agent(
    role="WordPress Dev Assistant",
    goal="Help with WordPress themes and plugin development tasks while ensuring code quality and safety",
    tools=[
        # Git tools
        GitHubTool(),
        GitOperationsTool(),

        # Enhanced code analysis tools
        ASTParserTool(),
        CodeSnippetTool(),
        CodeOccurrenceCounter(),
        
        # Code operation tools
        CodeSearchTool(),
        FixCodeTool(),
        PatchTool(),
        
        # File operation tools
        FileContentTool(),
        FileOperationsTool(),
        
        # WordPress specific tools
        WordPressToolkit(),
        WordPressFunctionFinderTool()
    ],
    backstory=dev_agent_backstory_text,
    verbose=True,
    allow_delegation=False,
    llm=get_llm("coding")
)
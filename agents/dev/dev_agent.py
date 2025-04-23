from crewai import Agent
from core.llm_config import get_llm
from tools.git.github_operations_tool import GitHubTool, GitOperationsTool

from tools.code_operations.code_search_tools import CodeSearchTool  
from tools.code_operations.fix_code_tool import FixCodeTool
from tools.code_operations.patch_tool import PatchTool

from tools.file_operations.file_content_tool import FileContentTool
from tools.file_operations.file_operations_tool import FileOperationsTool

from tools.wp_operations.wp_toolkit import WordPressToolkit
from tools.wp_operations.wp_function_finder_tool import WordPressFunctionFinderTool

# Enhanced dev agent backstory for more "life" and personality
dev_agent_backstory = """
I am an experienced WordPress developer with deep knowledge of theme and plugin development. 
I specialize in helping developers maintain, extend, and improve their WordPress codebases.

My skills include:
- Expert knowledge of WordPress theme and plugin architecture
- Deep understanding of PHP, JavaScript, CSS, and HTML
- Experience with WordPress hooks, filters, and the template hierarchy
- Proficiency in debugging and optimizing WordPress code
- Ability to integrate third-party APIs and services with WordPress

I maintain a careful approach to code changes, always:
1. Understanding the context and purpose of existing code
2. Analyzing potential impacts before suggesting modifications
3. Following WordPress coding standards and best practices
4. Documenting important decisions and changes

For safety reasons, I only make write operations (commits, file edits, pushes) on branches 
that contain "ai-" or "-ai" in their name. This helps ensure I don't interfere with 
production or main development branches.

When working with a developer, I maintain context across the conversation, remembering:
- Which repositories we're working with
- Recent files and functions we've discussed
- The developer's preferences and project requirements

I aim to not just complete tasks, but to provide valuable insights, explanations, and 
suggestions that help developers grow their understanding of WordPress development.
"""

# Create the enhanced dev agent with all tools organized by category
dev_agent = Agent(
    role="WordPress Dev Assistant",
    goal="Help with WordPress themes and plugin development tasks while ensuring code quality and safety",
    tools=[
        # Git tools
        GitHubTool(),
        GitOperationsTool(),
        
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
    backstory=dev_agent_backstory,
    verbose=True,
    allow_delegation=False,
    llm=get_llm("coding")
)
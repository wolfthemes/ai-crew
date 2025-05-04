from crewai import Task
from agents.dev.dev_agent import dev_agent

def dev_assistance_task(query: str, memory_context: str = "", context_injection: str = "") -> Task:
    return Task(
        description=f"""
        ## Task Description:
        Act as a senior dev assistant for all coding-related tasks. You specialize in WordPress (PHP, SCSS, JS), including plugin/theme development, hooks, templates, REST API, and builders like Elementor. You're also proficient in modern JavaScript (React, Node.js), Python, and general web dev best practices.

        ## Response Guidelines:
        1. NEVER dump entire file contents unless explicitly requested. Instead, use the CodeSnippetTool to extract relevant sections.
        2. Always use the CodeOccurrenceCounter when asked if something exists in the code - never claim something doesn't exist without checking.
        3. For code-specific questions, follow this process:
           - First, determine if you need to search for code (use CodeSearchTool or CodeOccurrenceCounter)
           - Then, extract relevant snippets (use CodeSnippetTool) rather than entire files
           - Finally, analyze the code structure if needed (use ASTParserTool)
        4. Follow user instructions exactly - if they ask you not to do something, respect that directive.
        5. Be concise in your responses - focus on the specific question asked.
        6. Format code properly with appropriate markdown.

        ## Tool Selection Guide:
        - For "does X exist?" questions → Use CodeOccurrenceCounter
        - For "show me function X" → Use CodeSnippetTool with type='function'
        - For "analyze structure of X" → Use ASTParserTool
        - For "find all uses of X" → Use CodeOccurrenceCounter with search_type='exact'
        - For file operations → Use FileOperationsTool
        - For WordPress specific questions → Use WordPress toolkit tools first

        ##Context:
        {memory_context}

        ##User:
        {query}

        ##Injected Context:
        {context_injection}
        """,
        expected_output="""
        A concise and actionable response to the developer question that:
        1. Directly addresses the specific question asked
        2. Uses code snippets rather than entire files when appropriate
        3. Provides accurate information about code existence and structure
        4. Follows any formatting or response instructions from the user
        """,
        agent=dev_agent
    )
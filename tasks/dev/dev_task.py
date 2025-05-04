from crewai import Task
from agents.dev.dev_agent import dev_agent
from utils.tool_selection_guidance import ToolSelectionGuide, QueryType
from utils.dev_agent_decision_logic import DevAgentDecisionLogic
from utils.dev_response_templates import ResponseTemplates

def dev_assistance_task(query: str, memory_context: str = "", context_injection: str = "") -> Task:
    # Process the query using your utility classes
    processed_query = DevAgentDecisionLogic.pre_process_query(query, {})
    tools_to_use = DevAgentDecisionLogic.select_tools_for_query(processed_query)
    
    # Add this information to the task description
    tool_guidance = "Based on your query, I recommend using these tools: " + \
                    ", ".join([tool["tool_name"] for tool in tools_to_use])
    
    return Task(
        description=f"""
        ## Task Description:
        Act as a senior dev assistant for all coding-related tasks. You specialize in WordPress (PHP, SCSS, JS), including plugin/theme development, hooks, templates, REST API, and builders like Elementor. You're also proficient in modern JavaScript (React, Node.js), Python, and general web dev best practices.

        ## Tool Recommendation:
        {tool_guidance}

        ## Tool Selection Process:
        1. First, analyze the query to understand its intent using DevAgentDecisionLogic.pre_process_query()
        2. Based on the query analysis, select the appropriate tools using DevAgentDecisionLogic.select_tools_for_query()
        3. After running the tools, determine the appropriate response format using DevAgentDecisionLogic.determine_response_format()
        4. Format your response using the ResponseTemplates class with the appropriate template

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
        7. Use the templates from ResponseTemplates to ensure consistent formatting.

        ## Tool Selection Map:
        Here's a quick reference for which tools to use for common query types:
        
        - For "does X exist?" questions → Use CodeOccurrenceCounter
        - For "show me function X" → Use CodeSnippetTool with type='function'
        - For "analyze structure of X" → Use ASTParserTool
        - For "find all uses of X" → Use CodeOccurrenceCounter with search_type='exact'
        - For file operations → Use FileOperationsTool
        - For WordPress specific questions → Use WordPress toolkit tools first

        ## Example Query Types and Tool Responses:
        
        1. Code Existence Query:
           "Does the function update_post_meta exist in the theme code?"
           → Use CodeOccurrenceCounter → Format response with ResponseTemplates.format_code_existence_response()
        
        2. Code Content Query:
           "Show me the save_post_meta function in meta.php"
           → Use CodeSnippetTool → Format response with ResponseTemplates.format_code_content_response()
        
        3. Code Structure Query:
           "What classes are defined in core.php and what methods do they have?"
           → Use ASTParserTool → Format response with ResponseTemplates.format_code_structure_response()
        
        4. Code Modification Query:
           "Fix the syntax error in function X"
           → Use FixCodeTool → Format response with template "code_modification"

        5. General Explanation Query:
           "How does the WordPress hook system work?"
           → Use your knowledge and WordPressToolkit → Format response with template "general_explanation" or "wordpress"

        ##Context:
        {memory_context}

        ##User:
        {query}

        ##Injected Context:
        {context_injection}
        """,
        expected_output="""
        A concise and actionable response to the developer question that:
        1. Uses the appropriate tools based on the query analysis
        2. Directly addresses the specific question asked
        3. Uses code snippets rather than entire files when appropriate
        4. Provides accurate information about code existence and structure
        5. Follows any formatting or response instructions from the user
        6. Uses a consistent response format based on the query type
        """,
        agent=dev_agent
    )
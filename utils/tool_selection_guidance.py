from enum import Enum
from typing import List, Dict, Any, Optional
import re
from pydantic import BaseModel, Field


class QueryType(Enum):
    CODE_EXISTENCE = "code_existence"
    CODE_CONTENT = "code_content"
    CODE_STRUCTURE = "code_structure"
    CODE_MODIFICATION = "code_modification"
    FILE_OPERATION = "file_operation"
    GIT_OPERATION = "git_operation"
    WORDPRESS_SPECIFIC = "wordpress_specific"
    GENERAL_EXPLANATION = "general_explanation"


class ToolSelectionGuide:
    """
    Guides the dev agent in selecting the appropriate tool based on the query type.
    This ensures consistent and effective tool usage for different types of queries.
    """
    
    # Mapping of query types to relevant tools
    TOOL_MAPPING = {
        QueryType.CODE_EXISTENCE: [
            {
                "tool_name": "code_occurrence_counter",
                "description": "Find and count occurrences of specific code elements",
                "priority": 1,
                "example_queries": [
                    "Does function X exist?",
                    "How many times is X used?",
                    "Where is X defined?",
                    "Find all uses of X"
                ]
            },
            {
                "tool_name": "code_search_tool",
                "description": "Search for patterns across multiple files",
                "priority": 2,
                "example_queries": [
                    "Which files contain X?",
                    "Find all files that use X"
                ]
            }
        ],
        QueryType.CODE_CONTENT: [
            {
                "tool_name": "code_snippet_tool",
                "description": "Extract specific parts of code files",
                "priority": 1,
                "example_queries": [
                    "Show me function X",
                    "Show the class Y",
                    "Show lines 10-20 of file Z"
                ]
            },
            {
                "tool_name": "file_content_tool",
                "description": "Get content of entire files (only when explicitly requested)",
                "priority": 2,
                "example_queries": [
                    "Show me the entire file",
                    "Get all contents of X"
                ]
            }
        ],
        QueryType.CODE_STRUCTURE: [
            {
                "tool_name": "ast_parser_tool",
                "description": "Analyze code structure and relationships",
                "priority": 1,
                "example_queries": [
                    "What classes are in this file?",
                    "List all functions in X",
                    "Show me the structure of class Y",
                    "What methods does class Z have?"
                ]
            }
        ],
        QueryType.CODE_MODIFICATION: [
            {
                "tool_name": "fix_code_tool",
                "description": "Debug and fix code issues",
                "priority": 1,
                "example_queries": [
                    "Fix this code",
                    "Debug this function",
                    "Improve performance of X"
                ]
            },
            {
                "tool_name": "patch_tool",
                "description": "Make specific changes to code",
                "priority": 2,
                "example_queries": [
                    "Replace X with Y",
                    "Update this function to do Z",
                    "Change the value of X"
                ]
            }
        ],
        QueryType.FILE_OPERATION: [
            {
                "tool_name": "file_operations_tool",
                "description": "Create, delete, or modify files",
                "priority": 1,
                "example_queries": [
                    "Create a new file",
                    "Delete file X",
                    "Rename Y to Z"
                ]
            }
        ],
        QueryType.GIT_OPERATION: [
            {
                "tool_name": "git_operations_tool",
                "description": "Perform git operations",
                "priority": 1,
                "example_queries": [
                    "Commit these changes",
                    "Create a new branch",
                    "Push to remote"
                ]
            },
            {
                "tool_name": "github_tool",
                "description": "Interact with GitHub API",
                "priority": 2,
                "example_queries": [
                    "Create a pull request",
                    "Get issue details",
                    "List repository branches"
                ]
            }
        ],
        QueryType.WORDPRESS_SPECIFIC: [
            {
                "tool_name": "wordpress_toolkit",
                "description": "WordPress-specific operations and searches",
                "priority": 1,
                "example_queries": [
                    "What hook should I use for X?",
                    "How do I modify the admin panel?",
                    "Which template file handles X?"
                ]
            },
            {
                "tool_name": "wordpress_function_finder_tool",
                "description": "Find WordPress function references",
                "priority": 2,
                "example_queries": [
                    "How do I use get_posts?",
                    "What arguments does register_post_type take?",
                    "Find WordPress function for X"
                ]
            }
        ],
        QueryType.GENERAL_EXPLANATION: []  # No specific tools needed, use agent's knowledge
    }
    
    # Query classification patterns
    QUERY_PATTERNS = {
        QueryType.CODE_EXISTENCE: [
            r"(?:does|is there|find|search).*?\b(function|class|method|variable|hook|constant)\b",
            r"(?:does|is there|find|search).*?\bexist",
            r"(?:where|how many times).*?\b(used|called|referenced|defined)",
            r"(?:find|search for).*?\boccurrence",
            r"(?:find|search for).*?\busage",
            r"(?:all|every).*?\b(instance|occurrence)",
        ],
        QueryType.CODE_CONTENT: [
            r"(?:show|get|display|see).*?\b(function|class|method)",
            r"(?:show|get|display|see).*?\b(code|implementation)",
            r"(?:show|get|display|see).*?\blines",
            r"(?:show|get|display|see).*?\bfile",
            r"(?:what does).*?\b(function|class|method).*?\bdo",
            r"(?:how does).*?\b(function|class|method).*?\bwork",
            r"(?:content of).*?\bfile",
        ],
        QueryType.CODE_STRUCTURE: [
            r"(?:what|which).*?\b(classes|functions|methods|variables)",
            r"(?:list|all).*?\b(classes|functions|methods|variables)",
            r"(?:structure|relationship|hierarchy|inheritance)",
            r"(?:what|which).*?\b(parameters|arguments|returns|properties)",
            r"(?:analyze|understand).*?\b(structure|architecture|design)",
            r"(?:how does).*?\b(class|component).*?\b(relate|inherit)",
        ],
        QueryType.CODE_MODIFICATION: [
            r"(?:fix|repair|debug|solve).*?\b(bug|issue|error|problem)",
            r"(?:change|modify|update|improve).*?\b(code|function|method|class)",
            r"(?:refactor|optimize|clean up)",
            r"(?:implement|add).*?\b(feature|functionality)",
            r"(?:write|create).*?\b(function|method|class)",
        ],
        QueryType.FILE_OPERATION: [
            r"(?:create|make|add).*?\b(file|directory|folder)",
            r"(?:delete|remove).*?\b(file|directory|folder)",
            r"(?:rename|move|copy).*?\b(file|directory|folder)",
            r"(?:write to|save).*?\bfile",
        ],
        QueryType.GIT_OPERATION: [
            r"(?:commit|push|pull|merge|rebase)",
            r"(?:git|github)",
            r"(?:branch|repository|repo)",
            r"(?:create|make).*?\b(pull request|PR)",
            r"(?:create|make).*?\b(branch)",
        ],
        QueryType.WORDPRESS_SPECIFIC: [
            r"(?:wordpress|wp)",
            r"(?:action|filter|hook)",
            r"(?:plugin|theme)",
            r"(?:gutenberg|elementor|woocommerce)",
            r"(?:template|shortcode|widget)",
            r"(?:admin|dashboard)",
        ],
        QueryType.GENERAL_EXPLANATION: [
            r"(?:explain|what is|how does|describe)",
            r"(?:why|when|where).*?\b(use|needed|required)",
            r"(?:best practice|recommendation|suggestion)",
            r"(?:difference between|compare)",
            r"(?:purpose of|reason for)",
        ]
    }
    
    @classmethod
    def classify_query(cls, query: str) -> List[QueryType]:
        """
        Classify the query into one or more query types.
        Returns a list of query types in order of relevance.
        """
        query_lower = query.lower()
        scores = {query_type: 0 for query_type in QueryType}
        
        # Check each pattern for each query type
        for query_type, patterns in cls.QUERY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    scores[query_type] += len(matches)
        
        # Sort query types by score (descending)
        sorted_types = sorted(
            [(query_type, score) for query_type, score in scores.items() if score > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return query types in order of relevance
        return [query_type for query_type, _ in sorted_types]
    
    @classmethod
    def get_recommended_tools(cls, query: str) -> List[Dict[str, Any]]:
        """
        Get recommended tools for the given query.
        Returns a list of tools in order of relevance.
        """
        query_types = cls.classify_query(query)
        
        if not query_types:
            # Default to general explanation if no specific type is detected
            query_types = [QueryType.GENERAL_EXPLANATION]
        
        # Collect tools for all query types
        tools = []
        for query_type in query_types:
            type_tools = cls.TOOL_MAPPING.get(query_type, [])
            for tool in type_tools:
                # Add query type to the tool info
                tool_with_type = tool.copy()
                tool_with_type["query_type"] = query_type.value
                tools.append(tool_with_type)
        
        # Remove duplicates (keeping the one with highest priority)
        unique_tools = {}
        for tool in tools:
            tool_name = tool["tool_name"]
            if tool_name not in unique_tools or tool["priority"] < unique_tools[tool_name]["priority"]:
                unique_tools[tool_name] = tool
        
        # Sort by priority (lower is better)
        return sorted(unique_tools.values(), key=lambda x: x["priority"])
    
    @classmethod
    def get_tool_usage_example(cls, tool_name: str, query: str) -> str:
        """
        Get an example of how to use the specified tool for a query similar to the given one.
        """
        # Map tool names to example usage templates
        tool_usage_examples = {
            "code_occurrence_counter": """
# Example usage of code_occurrence_counter
result = code_occurrence_counter(
    file_path="{file_path}",  # Path to file or "repo:{repo_name}" for whole repo
    search_term="{search_term}",  # What to search for
    search_type="exact",  # "exact", "regex", or "fuzzy"
    context_size=3  # Lines of context around matches
)
            """,
            "code_snippet_tool": """
# Example usage of code_snippet_tool
result = code_snippet_tool(
    file_path="{file_path}",
    query_type="{query_type}",  # "function", "class", "pattern", "lines", or "section"
    target="{target}",  # Function/class name, pattern, or line range
    context_lines=2
)
            """,
            "ast_parser_tool": """
# Example usage of ast_parser_tool
result = ast_parser_tool(
    file_path="{file_path}",
    query_type="{query_type}",  # "functions", "classes", "imports", "function_details", etc.
    target_name="{target_name}"  # Optional, only for targeted queries
)
            """,
            "file_content_tool": """
# Example usage of file_content_tool
result = file_content_tool(
    file_path="{file_path}"
)
            """,
            "fix_code_tool": """
# Example usage of fix_code_tool
result = fix_code_tool(
    file_path="{file_path}",
    issue_description="{issue_description}"
)
            """,
            "patch_tool": """
# Example usage of patch_tool
result = patch_tool(
    file_path="{file_path}",
    original_code="{original_code}",
    updated_code="{updated_code}"
)
            """,
            "file_operations_tool": """
# Example usage of file_operations_tool
result = file_operations_tool(
    operation="{operation}",  # "create", "read", "update", "delete", "list"
    file_path="{file_path}",
    content="{content}"  # Optional, for create/update operations
)
            """,
            "git_operations_tool": """
# Example usage of git_operations_tool
result = git_operations_tool(
    operation="{operation}",  # "commit", "branch", "checkout", "push", etc.
    repo_path="{repo_path}",
    message="{message}",  # For commit operations
    branch_name="{branch_name}"  # For branch operations
)
            """,
            "github_tool": """
# Example usage of github_tool
result = github_tool(
    operation="{operation}",  # "create_pr", "get_issue", "list_branches", etc.
    repo="{repo}",
    title="{title}",  # For PR/issue operations
    body="{body}"  # For PR/issue operations
)
            """,
            "wordpress_toolkit": """
# Example usage of wordpress_toolkit
result = wordpress_toolkit(
    operation="{operation}",  # "find_hook", "get_template", "check_function", etc.
    query="{query}"
)
            """,
            "wordpress_function_finder_tool": """
# Example usage of wordpress_function_finder_tool
result = wordpress_function_finder_tool(
    function_name="{function_name}"
)
            """
        }
        
        # Extract relevant parameters from the query
        # This is a simplified version, in practice you would need more sophisticated parsing
        file_path = "example_file.php"  # Default value
        search_term = "example_function"  # Default value
        
        # Check for file path in query
        file_path_match = re.search(r'\b([\w\-\.]+\.(php|py|js|html|css))\b', query)
        if file_path_match:
            file_path = file_path_match.group(1)
        
        # Check for function/class/variable name in query
        code_elem_match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s*\(|\s+function|\s+class|\s+variable)', query)
        if code_elem_match:
            search_term = code_elem_match.group(1)
        
        # Get the template for the specified tool
        template = tool_usage_examples.get(tool_name, "# No example available for this tool")
        
        # Fill in the template with extracted parameters
        formatted_example = template.format(
            file_path=file_path,
            search_term=search_term,
            query_type="functions",  # Default value
            target=search_term,
            target_name=search_term,
            issue_description="Fix syntax error",
            original_code="function example() { return }",
            updated_code="function example() { return true; }",
            operation="read",
            content="Example content",
            repo_path="repos/example",
            message="Fix bug",
            branch_name="feature/example",
            repo="example_repo",
            title="Example PR",
            body="Example description",
            query="find hook for post save",
            function_name=search_term
        )
        
        return formatted_example
import re
from typing import Dict, List, Any, Optional
from .tool_selection_guidance import ToolSelectionGuide, QueryType

class DevAgentDecisionLogic:
    """
    Decision logic for the dev agent to determine how to handle queries and select tools.
    This helps ensure the agent responds consistently and appropriately to different query types.
    """
    
    @staticmethod
    def pre_process_query(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-process the query to understand its intent and prepare for tool selection.
        
        Args:
            query: The user's query
            context: Dictionary containing context about the current state (repo, file, etc.)
            
        Returns:
            Dictionary with processed query information
        """
        # Initialize result
        result = {
            "original_query": query,
            "processed_query": query,
            "query_types": [],
            "recommended_tools": [],
            "identified_code_elements": [],
            "identified_files": [],
            "explicit_instructions": [],
            "example_tools_usage": {}
        }
        
        # Detect and extract explicit instructions
        explicit_instructions = DevAgentDecisionLogic._extract_explicit_instructions(query)
        result["explicit_instructions"] = explicit_instructions
        
        # Identify code elements (functions, classes, variables)
        code_elements = DevAgentDecisionLogic._identify_code_elements(query)
        result["identified_code_elements"] = code_elements
        
        # Identify files mentioned in the query
        files = DevAgentDecisionLogic._identify_files(query, context.get("repo", ""))
        result["identified_files"] = files
        
        # Get query classification and recommended tools
        query_types = ToolSelectionGuide.classify_query(query)
        result["query_types"] = [qt.value for qt in query_types]
        
        recommended_tools = ToolSelectionGuide.get_recommended_tools(query)
        result["recommended_tools"] = recommended_tools
        
        # Get example usage for each recommended tool
        for tool in recommended_tools:
            tool_name = tool["tool_name"]
            example = ToolSelectionGuide.get_tool_usage_example(tool_name, query)
            result["example_tools_usage"][tool_name] = example
        
        return result
    
    @staticmethod
    def select_tools_for_query(processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select the appropriate tools for the query based on its classification.
        
        Args:
            processed_query: The pre-processed query information
            
        Returns:
            List of tools to use, in the order they should be used
        """
        tools_to_use = []
        
        # Extract info from processed query
        query_types = processed_query["query_types"]
        recommended_tools = processed_query["recommended_tools"]
        explicit_instructions = processed_query["explicit_instructions"]
        code_elements = processed_query["identified_code_elements"]
        files = processed_query["identified_files"]
        
        # Override with explicit instructions if present
        if "use_tool" in explicit_instructions:
            tool_name = explicit_instructions["use_tool"]
            # Find the tool in the recommended tools
            for tool in recommended_tools:
                if tool["tool_name"] == tool_name:
                    tools_to_use.append(tool)
                    break
            
            # If tool not found in recommended, add it anyway (user requested it)
            if not tools_to_use:
                tools_to_use.append({
                    "tool_name": tool_name,
                    "priority": 1,
                    "query_type": "explicit_request"
                })
                
            return tools_to_use
        
        # Handle normal tool selection based on query type
        if query_types and recommended_tools:
            # Special case handling for specific query types
            if "code_existence" in query_types and code_elements:
                # For code existence queries with identified elements, strongly prefer code_occurrence_counter
                tools_to_use.append({
                    "tool_name": "code_occurrence_counter",
                    "priority": 1,
                    "query_type": "code_existence",
                    "parameters": {
                        "search_term": code_elements[0],  # Use the first identified code element
                        "file_path": files[0] if files else "repo:current",
                        "search_type": "exact"
                    }
                })
            elif "code_content" in query_types and code_elements:
                # For code content queries with identified elements, prefer code_snippet_tool over file_content_tool
                query_type = "function" if "function" in processed_query["original_query"].lower() else \
                            "class" if "class" in processed_query["original_query"].lower() else \
                            "pattern"
                            
                tools_to_use.append({
                    "tool_name": "code_snippet_tool",
                    "priority": 1,
                    "query_type": "code_content",
                    "parameters": {
                        "query_type": query_type,
                        "target": code_elements[0],  # Use the first identified code element
                        "file_path": files[0] if files else "search_needed"
                    }
                })
            else:
                # Use the recommended tools in order
                tools_to_use = recommended_tools[:2]  # Limit to top 2 tools
        
        # If no tools selected yet, fallback to first recommended tool or general explanation
        if not tools_to_use and recommended_tools:
            tools_to_use = [recommended_tools[0]]
        
        return tools_to_use
    
    @staticmethod
    def determine_response_format(processed_query: Dict[str, Any], tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine how to format the response based on the query and tool results.
        
        Args:
            processed_query: The pre-processed query information
            tool_results: Results from running the selected tools
            
        Returns:
            Dictionary with response format guidance
        """
        query_types = processed_query["query_types"]
        explicit_instructions = processed_query["explicit_instructions"]
        original_query = processed_query["original_query"]
        
        # Initialize response format
        response_format = {
            "include_code_snippets": True,  # Default to including code snippets
            "include_tool_results": True,   # Default to including tool results
            "include_explanation": True,    # Default to including explanation
            "max_snippet_length": 50,       # Default max snippet length (lines)
            "format": "markdown"            # Default format
        }
        
        # Apply explicit instructions from user
        if "no_explanation" in explicit_instructions:
            response_format["include_explanation"] = False
            
        if "only_code" in explicit_instructions:
            response_format["include_explanation"] = False
            response_format["include_tool_results"] = False
            
        if "no_code" in explicit_instructions:
            response_format["include_code_snippets"] = False
            
        # Adjust based on query type
        if "code_content" in query_types:
            # For code content queries, prioritize code snippets
            response_format["include_code_snippets"] = True
            response_format["max_snippet_length"] = 100  # Allow longer snippets
            
            # Check if user specifically asked for entire file
            if "entire file" in original_query.lower() or "whole file" in original_query.lower():
                response_format["max_snippet_length"] = 1000  # Very long for entire files
                
        elif "general_explanation" in query_types:
            # For explanation queries, prioritize explanation
            response_format["include_explanation"] = True
            response_format["include_code_snippets"] = False
            
        # Check for requests to format output in a specific way
        if "format as" in original_query.lower():
            format_match = re.search(r'format as (\w+)', original_query.lower())
            if format_match:
                requested_format = format_match.group(1)
                if requested_format in ["table", "list", "json", "plain"]:
                    response_format["format"] = requested_format
        
        return response_format
    
    @staticmethod
    def _extract_explicit_instructions(query: str) -> Dict[str, Any]:
        """Extract explicit instructions from the query."""
        instructions = {}
        
        # Check for explicit tool usage instructions
        tool_match = re.search(r'use (?:the )?([\w_]+)(?:\s+tool)?', query.lower())
        if tool_match:
            instructions["use_tool"] = tool_match.group(1)
            
        # Check for content formatting instructions
        if re.search(r'don\'t explain|no explanation', query.lower()):
            instructions["no_explanation"] = True
            
        if re.search(r'only (?:show|include|display) (?:the )?code', query.lower()):
            instructions["only_code"] = True
            
        if re.search(r'don\'t (?:show|include|display) (?:any )?code', query.lower()):
            instructions["no_code"] = True
            
        return instructions
    
    @staticmethod
    def _identify_code_elements(query: str) -> List[str]:
        """Identify code elements (functions, classes, variables) in the query."""
        elements = []
        
        # Match function names (potentially with parameters)
        function_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)', query)
        elements.extend(function_matches)
        
        # Match function/class/variable names mentioned with keywords
        keyword_matches = re.findall(r'(function|class|method|variable)\s+([a-zA-Z_][a-zA-Z0-9_]*)', query)
        elements.extend([m[1] for m in keyword_matches])
        
        # Match other potential code elements (simple identifiers)
        if not elements:
            # Only look for other identifiers if no functions/classes found
            other_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]{2,})\b', query)
            # Filter common English words
            common_words = {"find", "search", "show", "get", "display", "function", "class", "variable", "method"}
            elements.extend([m for m in other_matches if m.lower() not in common_words])
        
        return elements
    
    @staticmethod
    def _identify_files(query: str, repo_context: str) -> List[str]:
        """Identify file references in the query."""
        files = []
        
        # Match explicit file paths
        file_matches = re.findall(r'\b([\w\-./]+\.(php|py|js|jsx|ts|tsx|html|css|scss))\b', query)
        files.extend([m[0] for m in file_matches])
        
        # Match file names without directories
        if not files:
            file_name_matches = re.findall(r'\b([\w\-]+\.(php|py|js|jsx|ts|tsx|html|css|scss))\b', query)
            files.extend([m[0] for m in file_name_matches])
        
        # If no files found and repo context is available, use a wildcard for the repo
        if not files and repo_context:
            files.append(f"repo:{repo_context}")
            
        return files
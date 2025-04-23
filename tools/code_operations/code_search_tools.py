from typing import Type, Literal
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re

REPO_ROOT = os.path.abspath("repos")

class CodeSearchInput(BaseModel):
    search_type: Literal["function", "hook", "class", "pattern"] = Field(
        default="function", 
        description="Type of search to perform"
    )
    search_term: str = Field(..., description="Function name, hook, class name or regex pattern to search for")
    repo_name: str = Field(..., description="Repository name to search in")
    file_path: str = Field(default=None, description="Optional specific file to search within")
    include_context: bool = Field(default=True, description="Include surrounding code context")
    case_sensitive: bool = Field(default=False, description="Whether search should be case sensitive")
    max_results: int = Field(default=10, description="Maximum number of results to return")

class CodeSearchTool(BaseTool):
    name: str = "code_search_tool"
    description: str = "Advanced search for functions, hooks, classes or patterns in WordPress codebase"
    args_schema: Type[BaseModel] = CodeSearchInput

    def _run(self, search_type: str, search_term: str, repo_name: str, file_path: str = None, 
             include_context: bool = True, case_sensitive: bool = False, max_results: int = 10) -> str:
        try:
            repo_path = os.path.join(REPO_ROOT, repo_name)
            
            if not os.path.exists(repo_path):
                return f"❌ Repository not found: {repo_path}"
            
            # Prepare the appropriate regex pattern based on search type
            pattern = self._create_search_pattern(search_type, search_term, case_sensitive)
            
            # Track matches across the codebase
            matches = []
            
            # Search single file if specified
            if file_path:
                full_path = os.path.join(repo_path, file_path)
                if os.path.isfile(full_path):
                    self._search_file(full_path, file_path, pattern, matches, include_context)
                else:
                    return f"❌ File not found: {full_path}"
            else:
                # Search all relevant files in the repo
                extensions = self._get_extensions_for_search_type(search_type)
                for root, _, files in os.walk(repo_path):
                    for file in files:
                        if file.endswith(extensions):
                            rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                            full_path = os.path.join(root, file)
                            self._search_file(full_path, rel_path, pattern, matches, include_context)
                            
                            # Stop if we've reached max results
                            if len(matches) >= max_results:
                                break
            
            # Return results
            if not matches:
                return f"No matches found for {search_type} '{search_term}' in {repo_name}"
            
            # Format and return results
            return self._format_results(search_type, search_term, repo_name, matches[:max_results])
            
        except Exception as e:
            return f"❌ Error during code search: {e}"
    
    def _create_search_pattern(self, search_type, search_term, case_sensitive):
        """Create appropriate regex pattern based on search type"""
        flags = 0 if case_sensitive else re.IGNORECASE
        
        if search_type == "function":
            # Pattern for PHP function definitions
            return re.compile(r'function\s+' + re.escape(search_term) + r'\s*\(', flags)
        
        elif search_type == "class":
            # Pattern for PHP class definitions
            return re.compile(r'class\s+' + re.escape(search_term) + r'\b', flags)
        
        elif search_type == "hook":
            # Pattern for WordPress hooks (add_action, add_filter)
            return re.compile(r'add_(action|filter)\s*\(\s*[\'"]' + re.escape(search_term) + r'[\'"]', flags)
        
        elif search_type == "pattern":
            # Use the search term as a regex pattern directly
            try:
                return re.compile(search_term, flags)
            except re.error:
                # If invalid regex, treat as literal text
                return re.compile(re.escape(search_term), flags)
        
        # Default fallback
        return re.compile(re.escape(search_term), flags)
    
    def _get_extensions_for_search_type(self, search_type):
        """Return file extensions to search based on search type"""
        if search_type in ["function", "class", "hook"]:
            return ('.php',)  # PHP files for WordPress functions, classes, hooks
        else:
            # For generic pattern search, include more file types
            return ('.php', '.js', '.css', '.html', '.txt', '.md')
    
    def _search_file(self, full_path, rel_path, pattern, matches, include_context):
        """Search a single file for the pattern and collect matches"""
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                # Find all matches of the pattern
                for match in pattern.finditer(content):
                    start_pos = match.start()
                    line_number = content[:start_pos].count('\n') + 1
                    
                    # Get the matched line
                    line_start = content.rfind('\n', 0, start_pos) + 1
                    line_end = content.find('\n', start_pos)
                    if line_end == -1:  # Last line without newline
                        line_end = len(content)
                    line = content[line_start:line_end].strip()
                    
                    # Add match info
                    match_info = {
                        'file': rel_path,
                        'line': line_number,
                        'text': line,
                        'start': start_pos
                    }
                    
                    # Add context if requested
                    if include_context:
                        context_start = max(0, content.rfind('\n', 0, max(0, start_pos - 150)) + 1)
                        context_end = min(len(content), content.find('\n', min(len(content), start_pos + 400)))
                        if context_end == -1:
                            context_end = len(content)
                        
                        match_info['context'] = content[context_start:context_end]
                    
                    matches.append(match_info)
        
        except Exception as e:
            # Add the error to matches for reporting
            matches.append({
                'file': rel_path,
                'error': str(e)
            })
    
    def _format_results(self, search_type, search_term, repo_name, matches):
        """Format search results for nice output"""
        result = f"# Search Results for {search_type} '{search_term}' in {repo_name}\n\n"
        
        for i, match in enumerate(matches, 1):
            if 'error' in match:
                result += f"## Error in {match['file']}:\n{match['error']}\n\n"
                continue
                
            result += f"## Match {i}: {match['file']}:{match['line']}\n\n"
            result += f"```php\n{match['text']}\n```\n\n"
            
            if 'context' in match:
                result += f"### Context:\n\n```php\n{match['context']}\n```\n\n"
            
            result += "---\n\n"
        
        return result

    def run(self, query: str) -> str:
        return "Use structured input with 'search_type', 'search_term', 'repo_name', and optional parameters."
from typing import Type, Literal
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re

REPO_ROOT = os.path.abspath("repos")

class FunctionSearchInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    file_path: str = Field(default=None, description="Specific file to search (optional)")
    function_name: str = Field(..., description="Function name to search for")
    search_type: Literal["exact", "partial"] = Field(default="exact", description="Search type: exact or partial match")

class WordPressFunctionFinderTool(BaseTool):
    name: str = "wp_function_finder_tool"
    description: str = "Finds PHP functions in WordPress theme/plugin files"
    args_schema: Type[BaseModel] = FunctionSearchInput

    def _run(self, repo_name: str, function_name: str, file_path: str = None, search_type: str = "exact") -> str:
        try:
            repo_path = os.path.join(REPO_ROOT, repo_name)
            
            if not os.path.isdir(repo_path):
                return f"❌ Repository not found: {repo_path}"
            
            results = []
            
            # Prepare search pattern based on search type
            if search_type == "exact":
                function_pattern = re.compile(r'function\s+' + re.escape(function_name) + r'\s*\(', re.IGNORECASE)
                call_pattern = re.compile(r'(?<!\w)' + re.escape(function_name) + r'\s*\(', re.IGNORECASE)
            else:
                function_pattern = re.compile(r'function\s+\w*' + re.escape(function_name) + r'\w*\s*\(', re.IGNORECASE)
                call_pattern = re.compile(r'(?<!\w)\w*' + re.escape(function_name) + r'\w*\s*\(', re.IGNORECASE)
            
            # If specific file given, search only that file
            if file_path:
                full_path = os.path.join(repo_path, file_path)
                if os.path.isfile(full_path) and full_path.endswith('.php'):
                    self._search_file(full_path, file_path, function_pattern, call_pattern, results)
            else:
                # Search all PHP files in the repo
                for root, _, files in os.walk(repo_path):
                    for file in files:
                        if file.endswith('.php'):
                            relative_path = os.path.relpath(os.path.join(root, file), repo_path)
                            full_path = os.path.join(root, file)
                            self._search_file(full_path, relative_path, function_pattern, call_pattern, results)
            
            if not results:
                return f"❌ No functions matching '{function_name}' found in {repo_name}"
            
            return "Function search results:\n\n" + "\n\n".join(results)
        
        except Exception as e:
            return f"❌ Error searching for functions: {e}"
    
    def _search_file(self, full_path, relative_path, function_pattern, call_pattern, results):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                # Find function definitions
                function_matches = []
                for match in function_pattern.finditer(content):
                    start = match.start()
                    # Get the line number
                    line_number = content[:start].count('\n') + 1
                    
                    # Extract the function with its body
                    # This is a simplified approach - might need improvement for complex functions
                    start_pos = content.rfind('\n', 0, start) + 1 if start > 0 else 0
                    line = content[start_pos:content.find('\n', start)].strip()
                    
                    function_matches.append(f"Line {line_number}: {line}")
                
                if function_matches:
                    results.append(f"File: {relative_path}\nFunction definitions:\n" + 
                                  "\n".join(function_matches))
                    
                    # Get context around the function
                    for match in function_pattern.finditer(content):
                        start = match.start()
                        # Extract more context to include the function body
                        context_start = max(0, start - 200)
                        context_end = min(len(content), start + 1000)
                        
                        # Try to find opening and closing braces to capture the whole function
                        open_braces = 0
                        in_function = False
                        function_body = []
                        
                        for i in range(start, context_end):
                            if content[i] == '{':
                                if not in_function:
                                    in_function = True
                                open_braces += 1
                            elif content[i] == '}':
                                open_braces -= 1
                                if open_braces == 0 and in_function:
                                    function_body.append(content[i])
                                    break
                            
                            if in_function:
                                function_body.append(content[i])
                        
                        context = content[context_start:start] + ''.join(function_body)
                        results.append(f"Context for function in {relative_path}:\n```php\n{context}\n```")
                
                # Find function calls
                call_matches = []
                for match in call_pattern.finditer(content):
                    if function_pattern.search(content[match.start()-50:match.start()]) is None:  # Avoid duplicating definitions
                        start = match.start()
                        line_number = content[:start].count('\n') + 1
                        start_pos = content.rfind('\n', 0, start) + 1 if start > 0 else 0
                        line = content[start_pos:content.find('\n', start)].strip()
                        call_matches.append(f"Line {line_number}: {line}")
                
                if call_matches:
                    results.append(f"Function calls in {relative_path}:\n" + "\n".join(call_matches))
        
        except Exception as e:
            results.append(f"Error processing {relative_path}: {e}")

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_name', 'function_name', optional 'file_path', and 'search_type'."
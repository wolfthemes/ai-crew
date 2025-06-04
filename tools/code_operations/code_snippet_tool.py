from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re
from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_ROOT")

# Input schema
class CodeSnippetInput(BaseModel):
    repo_path: str = Field(..., description="The name of the repo (inside 'repos/')")
    file_path: str = Field(..., description="Relative path to the file inside the repo")
    query_type: str = Field(..., description="Type of query: 'function', 'class', 'pattern', 'lines', 'section'")
    target: str = Field(..., description="Name of function/class, regex pattern, or line range (e.g., '10-20')")
    context_lines: int = Field(2, description="Number of context lines to include before and after the match")

# CodeSnippetTool definition
class CodeSnippetTool(BaseTool):
    name: str = "code_snippet_tool"
    description: str = """
    Extract relevant code snippets from files instead of returning entire file contents.
    Use this tool to:
    - Get a specific function or method by name
    - Get a specific class by name
    - Find code matching a regex pattern
    - Get a specific range of lines
    - Get a logical section of code
    """
    args_schema: Type[BaseModel] = CodeSnippetInput

    def _detect_language(self, file_path: str) -> str:
        """Detect the programming language based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            '.py': 'python',
            '.php': 'php',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'css',
        }
        
        return language_map.get(ext, 'text')
    
    def _find_function(self, content: str, function_name: str, language: str) -> dict:
        """Find a function by name in the code content."""
        # Different regex patterns for different languages
        patterns = {
            'python': r'(def\s+' + re.escape(function_name) + r'\s*\([^)]*\):.*?)(?=\n\S|$)',
            'php': r'(function\s+' + re.escape(function_name) + r'\s*\([^)]*\)\s*{.*?})(?=\n\S|$)',
            'javascript': r'(function\s+' + re.escape(function_name) + r'\s*\([^)]*\)\s*{.*?}|const\s+' + 
                         re.escape(function_name) + r'\s*=\s*(?:function|\([^)]*\)\s*=>)\s*{.*?})(?=\n\S|$)',
        }
        
        # Default to a more generic pattern if language not specified
        pattern = patterns.get(language, r'((?:function|def)\s+' + re.escape(function_name) + r'\s*\([^)]*\).*?})(?=\n\S|$)')
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            # Get line numbers
            start_line = content[:match.start()].count('\n') + 1
            end_line = start_line + match.group(1).count('\n')
            
            return {
                'found': True,
                'snippet': match.group(1),
                'start_line': start_line,
                'end_line': end_line
            }
        
        # Try arrow functions in JavaScript
        if language == 'javascript':
            arrow_pattern = r'(const\s+' + re.escape(function_name) + r'\s*=\s*\([^)]*\)\s*=>\s*{.*?})(?=\n\S|$)'
            match = re.search(arrow_pattern, content, re.DOTALL)
            if match:
                start_line = content[:match.start()].count('\n') + 1
                end_line = start_line + match.group(1).count('\n')
                
                return {
                    'found': True,
                    'snippet': match.group(1),
                    'start_line': start_line,
                    'end_line': end_line
                }
        
        return {'found': False}
    
    def _find_class(self, content: str, class_name: str, language: str) -> dict:
        """Find a class by name in the code content."""
        patterns = {
            'python': r'(class\s+' + re.escape(class_name) + r'\s*(?:\([^)]*\))?\s*:.*?)(?=\n\S|$)',
            'php': r'(class\s+' + re.escape(class_name) + r'\s*(?:extends|implements|{).*?})(?=\n\S|$)',
            'javascript': r'(class\s+' + re.escape(class_name) + r'\s*(?:extends\s+[A-Za-z0-9_]+\s*)?{.*?})(?=\n\S|$)',
        }
        
        pattern = patterns.get(language, r'(class\s+' + re.escape(class_name) + r'\s*(?:{|:).*?)(?=\n\S|$)')
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            start_line = content[:match.start()].count('\n') + 1
            end_line = start_line + match.group(1).count('\n')
            
            return {
                'found': True,
                'snippet': match.group(1),
                'start_line': start_line,
                'end_line': end_line
            }
        
        return {'found': False}
    
    def _get_lines(self, content: str, line_range: str) -> dict:
        """Get a specific range of lines from the code content."""
        try:
            # Parse line range like '10-20'
            if '-' in line_range:
                start, end = map(int, line_range.split('-'))
            else:
                # Single line
                start = end = int(line_range)
                
            lines = content.split('\n')
            
            # Adjust for 0-based indexing and bounds
            start = max(1, min(start, len(lines)))
            end = max(start, min(end, len(lines)))
            
            # Extract lines
            snippet = '\n'.join(lines[start-1:end])
            
            return {
                'found': True,
                'snippet': snippet,
                'start_line': start,
                'end_line': end
            }
        except ValueError:
            return {'found': False, 'error': f"Invalid line range: {line_range}"}
    
    def _add_context_lines(self, content: str, start_line: int, end_line: int, context_lines: int) -> str:
        """Add context lines before and after the snippet."""
        lines = content.split('\n')
        
        # Calculate context bounds
        context_start = max(1, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines)
        
        # Extract with context
        return '\n'.join(lines[context_start-1:context_end])

    def _run(self, repo_path: str, file_path: str, query_type: str, target: str, context_lines: int = 2) -> str:
        full_path = os.path.join(REPO_ROOT, repo_path, file_path)

        if not os.path.exists(full_path):
            return f"❌ File not found: {full_path}"
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            language = self._detect_language(file_path)
            
            if query_type == 'function':
                result = self._find_function(content, target, language)
                
                if result['found']:
                    snippet_with_context = self._add_context_lines(
                        content, result['start_line'], result['end_line'], context_lines
                    )
                    
                    return f"Found function '{target}' (lines {result['start_line']}-{result['end_line']}):\n\n```{language}\n{snippet_with_context}\n```"
                else:
                    return f"❌ Function '{target}' not found in {file_path}."
                    
            elif query_type == 'class':
                result = self._find_class(content, target, language)
                
                if result['found']:
                    snippet_with_context = self._add_context_lines(
                        content, result['start_line'], result['end_line'], context_lines
                    )
                    
                    return f"Found class '{target}' (lines {result['start_line']}-{result['end_line']}):\n\n```{language}\n{snippet_with_context}\n```"
                else:
                    return f"❌ Class '{target}' not found in {file_path}."
                    
            elif query_type == 'lines':
                result = self._get_lines(content, target)
                
                if result['found']:
                    return f"Lines {target} from {file_path}:\n\n```{language}\n{result['snippet']}\n```"
                else:
                    return f"❌ Error: {result.get('error', 'Could not extract the specified lines.')}"
                    
            else:
                return f"❌ Unknown query_type '{query_type}'."
                
        except Exception as e:
            return f"❌ Error extracting from {file_path}: {str(e)}"
            
    def run(self, query: str) -> str:
        return "Use structured input with 'repo_path', 'file_path', 'query_type', 'target', and optional 'context_lines'."

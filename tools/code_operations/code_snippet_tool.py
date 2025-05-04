import os
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class CodeSnippetInput(BaseModel):
    """Input for the Code Snippet tool."""
    file_path: str = Field(..., description="Path to the file to extract snippets from")
    query_type: str = Field(..., description="Type of query: 'function', 'class', 'pattern', 'lines', 'section'")
    target: str = Field(..., description="Name of function/class, regex pattern, or line range (e.g., '10-20')")
    context_lines: int = Field(2, description="Number of context lines to include before and after the match")


class CodeSnippetTool(BaseTool):
    name = "code_snippet_tool"
    description = """
    Extract relevant code snippets from files instead of returning entire file contents.
    Use this tool to:
    - Get a specific function or method by name
    - Get a specific class by name
    - Find code matching a regex pattern
    - Get a specific range of lines
    - Get a logical section of code
    """
    args_schema = CodeSnippetInput
    
    def _find_function(self, content: str, function_name: str, language: str) -> Dict[str, Any]:
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
    
    def _find_class(self, content: str, class_name: str, language: str) -> Dict[str, Any]:
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
    
    def _find_pattern(self, content: str, pattern: str) -> List[Dict[str, Any]]:
        """Find all occurrences of a regex pattern in the code content."""
        try:
            regex = re.compile(pattern)
            matches = []
            
            for match in regex.finditer(content):
                start_line = content[:match.start()].count('\n') + 1
                end_line = start_line + match.group(0).count('\n')
                
                matches.append({
                    'snippet': match.group(0),
                    'start_line': start_line,
                    'end_line': end_line
                })
            
            return matches
        except re.error:
            # If regex is invalid, try as a plain text search
            results = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern in line:
                    results.append({
                        'snippet': line,
                        'start_line': i + 1,
                        'end_line': i + 1
                    })
            return results
    
    def _get_lines(self, content: str, line_range: str) -> Dict[str, Any]:
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
    
    def _get_section(self, content: str, section_name: str, language: str) -> Dict[str, Any]:
        """Get a logical section of code (e.g., PHP comment sections, HTML comment blocks)."""
        patterns = {
            'php': r'/\*\s*' + re.escape(section_name) + r'\s*\*/(.*?)(?:/\*|$)',
            'javascript': r'//\s*' + re.escape(section_name) + r'\s*\n(.*?)(?://|$)',
            'html': r'<!--\s*' + re.escape(section_name) + r'\s*-->(.*?)(?:<!--|$)',
            'python': r'#\s*' + re.escape(section_name) + r'\s*\n(.*?)(?:#|$)',
        }
        
        pattern = patterns.get(language, r'(?:/\*|//|#|<!--)\s*' + re.escape(section_name) + r'\s*(?:\*/|-->|\n)(.*?)(?:/\*|//|#|<!--|$)')
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            start_line = content[:match.start()].count('\n') + 1
            end_line = start_line + match.group(0).count('\n')
            
            return {
                'found': True,
                'snippet': match.group(0),
                'start_line': start_line,
                'end_line': end_line
            }
        
        return {'found': False}
    
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
        
        return language_map.get(ext, 'unknown')
    
    def _add_context_lines(self, content: str, start_line: int, end_line: int, context_lines: int) -> str:
        """Add context lines before and after the snippet."""
        lines = content.split('\n')
        
        # Calculate context bounds
        context_start = max(1, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines)
        
        # Extract with context
        return '\n'.join(lines[context_start-1:context_end])
    
    def _run(self, file_path: str, query_type: str, target: str, context_lines: int = 2) -> str:
        """Run the code snippet extraction with the given parameters."""
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
                    return f"Function '{target}' not found in {file_path}."
                    
            elif query_type == 'class':
                result = self._find_class(content, target, language)
                
                if result['found']:
                    snippet_with_context = self._add_context_lines(
                        content, result['start_line'], result['end_line'], context_lines
                    )
                    
                    return f"Found class '{target}' (lines {result['start_line']}-{result['end_line']}):\n\n```{language}\n{snippet_with_context}\n```"
                else:
                    return f"Class '{target}' not found in {file_path}."
                    
            elif query_type == 'pattern':
                matches = self._find_pattern(content, target)
                
                if matches:
                    results = [f"Found {len(matches)} matches for pattern '{target}' in {file_path}:"]
                    
                    for idx, match in enumerate(matches[:5]):  # Limit to first 5 matches
                        snippet_with_context = self._add_context_lines(
                            content, match['start_line'], match['end_line'], context_lines
                        )
                        results.append(f"\nMatch {idx+1} (lines {match['start_line']}-{match['end_line']}):\n```{language}\n{snippet_with_context}\n```")
                    
                    if len(matches) > 5:
                        results.append(f"\n...and {len(matches) - 5} more matches.")
                        
                    return "\n".join(results)
                else:
                    return f"Pattern '{target}' not found in {file_path}."
                    
            elif query_type == 'lines':
                result = self._get_lines(content, target)
                
                if result['found']:
                    return f"Lines {target} from {file_path}:\n\n```{language}\n{result['snippet']}\n```"
                else:
                    return f"Error: {result.get('error', 'Could not extract the specified lines.')}"
                    
            elif query_type == 'section':
                result = self._get_section(content, target, language)
                
                if result['found']:
                    snippet_with_context = self._add_context_lines(
                        content, result['start_line'], result['end_line'], context_lines
                    )
                    
                    return f"Found section '{target}' (lines {result['start_line']}-{result['end_line']}):\n\n```{language}\n{snippet_with_context}\n```"
                else:
                    return f"Section '{target}' not found in {file_path}."
                    
            else:
                return f"Error: Unknown query_type '{query_type}'."
                
        except Exception as e:
            return f"Error extracting from {file_path}: {str(e)}"
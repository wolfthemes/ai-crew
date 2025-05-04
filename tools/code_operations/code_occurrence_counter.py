import os
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class CodeOccurrenceInput(BaseModel):
    """Input for the Code Occurrence Counter tool."""
    file_path: str = Field(..., description="Path to the file to analyze or 'repo:' prefix to search entire repo")
    search_term: str = Field(..., description="Code element to search for (function name, variable, string, etc.)")
    search_type: str = Field("exact", description="Search type: 'exact', 'regex', 'fuzzy'")
    context_size: int = Field(3, description="Number of lines of context to include around each occurrence")


class CodeOccurrenceCounter(BaseTool):
    name = "code_occurrence_counter"
    description = """
    Count and list occurrences of specific code elements in files or repositories.
    Precisely answers questions about whether something exists in the code and where.
    
    Use this tool when asked:
    - "Does X exist in the code?"
    - "How many times is X used?"
    - "Where is X defined or used?"
    - "Find all occurrences of X"
    
    The tool can search:
    - A specific file with exact path
    - Multiple files matching a pattern
    - An entire repository
    """
    args_schema = CodeOccurrenceInput
    
    def _count_in_file(self, file_path: str, search_term: str, search_type: str) -> List[Dict[str, Any]]:
        """Count occurrences of a term in a single file."""
        if not os.path.exists(file_path):
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')
                
            occurrences = []
            
            # Choose search method based on search_type
            if search_type == 'exact':
                line_matches = [(i, line) for i, line in enumerate(lines) if search_term in line]
                
            elif search_type == 'regex':
                try:
                    pattern = re.compile(search_term)
                    line_matches = [(i, line) for i, line in enumerate(lines) if pattern.search(line)]
                except re.error:
                    return [{'error': f"Invalid regex pattern: {search_term}"}]
                    
            elif search_type == 'fuzzy':
                # Simple fuzzy matching (case insensitive)
                term_lower = search_term.lower()
                line_matches = [(i, line) for i, line in enumerate(lines) 
                               if term_lower in line.lower()]
            else:
                return [{'error': f"Unknown search type: {search_type}"}]
                
            # Process matches
            for line_num, line in line_matches:
                start_context = max(0, line_num - self.context_size)
                end_context = min(len(lines) - 1, line_num + self.context_size)
                
                context_lines = lines[start_context:end_context + 1]
                # Highlight the matched line
                context_lines[line_num - start_context] = f">>> {context_lines[line_num - start_context]}"
                
                occurrences.append({
                    'file': file_path,
                    'line': line_num + 1,  # 1-indexed line numbers
                    'content': line.strip(),
                    'context': '\n'.join(context_lines)
                })
                
            return occurrences
            
        except Exception as e:
            return [{'error': f"Error reading file {file_path}: {str(e)}"}]
    
    def _search_repo(self, repo_path: str, search_term: str, search_type: str, file_pattern: str = None) -> List[Dict[str, Any]]:
        """Search for occurrences across a repository or directory."""
        if not os.path.isdir(repo_path):
            return [{'error': f"Repository path not found: {repo_path}"}]
            
        all_occurrences = []
        
        # Extensions to search in code files
        code_extensions = ['.py', '.php', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', 
                           '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.rs', '.swift']
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                # Skip non-code files unless a specific pattern is provided
                if file_pattern:
                    if not re.search(file_pattern, file):
                        continue
                elif not any(file.endswith(ext) for ext in code_extensions):
                    continue
                    
                file_path = os.path.join(root, file)
                file_occurrences = self._count_in_file(file_path, search_term, search_type)
                all_occurrences.extend(file_occurrences)
                
        return all_occurrences
    
    def _run(self, file_path: str, search_term: str, search_type: str = "exact", context_size: int = 3) -> str:
        """Run the code occurrence counter with the given parameters."""
        self.context_size = context_size
        
        # Handle repository search
        if file_path.startswith('repo:'):
            repo_name = file_path[5:].strip()
            if not repo_name:
                return "Error: No repository name specified. Use format 'repo:repo_name'"
                
            repo_path = os.path.join("repos", repo_name)
            occurrences = self._search_repo(repo_path, search_term, search_type)
            
        # Handle file pattern search (with wildcards)
        elif '*' in file_path:
            base_dir = os.path.dirname(file_path) or '.'
            file_pattern = os.path.basename(file_path).replace('*', '.*')
            occurrences = self._search_repo(base_dir, search_term, search_type, file_pattern)
            
        # Handle single file search
        else:
            occurrences = self._count_in_file(file_path, search_term, search_type)
            
        # Process and format results
        if not occurrences:
            return f"No occurrences of '{search_term}' found."
            
        if 'error' in occurrences[0]:
            return f"Error: {occurrences[0]['error']}"
            
        result = f"Found {len(occurrences)} occurrences of '{search_term}':\n\n"
        
        for i, occ in enumerate(occurrences[:10]):  # Limit to 10 results
            result += f"Occurrence {i+1}: {occ['file']}:{occ['line']}\n"
            result += f"Context:\n```\n{occ['context']}\n```\n\n"
            
        if len(occurrences) > 10:
            result += f"... and {len(occurrences) - 10} more occurrences."
            
        return result
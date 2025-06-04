from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re
from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_ROOT")

# Input schema
class CodeOccurrenceInput(BaseModel):
    repo_path: str = Field(..., description="The name of the repo (inside 'repos/')")
    file_path: str = Field("", description="Relative path to the file inside the repo (blank for entire repo)")
    search_term: str = Field(..., description="Code element to search for (function name, variable, string, etc.)")
    search_type: str = Field("exact", description="Search type: 'exact', 'regex', 'fuzzy'")
    context_size: int = Field(3, description="Number of lines of context to include around each occurrence")

# CodeOccurrenceCounter definition
class CodeOccurrenceCounter(BaseTool):
    name: str = "code_occurrence_counter"
    description: str = """
    Count and list occurrences of specific code elements in files or repositories.
    Precisely answers questions about whether something exists in the code and where.
    
    Use this tool when asked:
    - "Does X exist in the code?"
    - "How many times is X used?"
    - "Where is X defined or used?"
    - "Find all occurrences of X"
    """
    args_schema: Type[BaseModel] = CodeOccurrenceInput

    def _count_in_file(self, file_path: str, search_term: str, search_type: str, context_size: int) -> list:
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
                start_context = max(0, line_num - context_size)
                end_context = min(len(lines) - 1, line_num + context_size)
                
                context_lines = lines[start_context:end_context + 1]
                # Highlight the matched line
                context_lines[line_num - start_context] = f">>> {context_lines[line_num - start_context]}"
                
                occurrences.append({
                    'file': os.path.basename(file_path),
                    'line': line_num + 1,  # 1-indexed line numbers
                    'content': line.strip(),
                    'context': '\n'.join(context_lines)
                })
                
            return occurrences
            
        except Exception as e:
            return [{'error': f"Error reading file {file_path}: {str(e)}"}]
    
    def _search_repo(self, repo_path: str, search_term: str, search_type: str, context_size: int) -> list:
        """Search for occurrences across a repository."""
        if not os.path.isdir(repo_path):
            return [{'error': f"Repository path not found: {repo_path}"}]
            
        all_occurrences = []
        
        # Extensions to search in code files
        code_extensions = ['.py', '.php', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss']
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if not any(file.endswith(ext) for ext in code_extensions):
                    continue
                    
                file_path = os.path.join(root, file)
                file_occurrences = self._count_in_file(file_path, search_term, search_type, context_size)
                
                # Add relative path to the repository
                for occ in file_occurrences:
                    if 'file' in occ:
                        occ['file'] = os.path.relpath(file_path, repo_path)
                
                all_occurrences.extend(file_occurrences)
                
        return all_occurrences

    def _run(self, repo_path: str, file_path: str, search_term: str, search_type: str = "exact", context_size: int = 3) -> str:
        repo_full_path = os.path.join(REPO_ROOT, repo_path)
        
        if not file_path:
            # Search entire repo
            occurrences = self._search_repo(repo_full_path, search_term, search_type, context_size)
        else:
            # Search single file
            file_full_path = os.path.join(repo_full_path, file_path)
            occurrences = self._count_in_file(file_full_path, search_term, search_type, context_size)
            
        # Process and format results
        if not occurrences:
            return f"❌ No occurrences of '{search_term}' found."
            
        if 'error' in occurrences[0]:
            return f"❌ Error: {occurrences[0]['error']}"
            
        result = f"✅ Found {len(occurrences)} occurrences of '{search_term}':\n\n"
        
        for i, occ in enumerate(occurrences[:10]):  # Limit to 10 results
            result += f"Occurrence {i+1}: {occ['file']}:{occ['line']}\n"
            result += f"Context:\n```\n{occ['context']}\n```\n\n"
            
        if len(occurrences) > 10:
            result += f"... and {len(occurrences) - 10} more occurrences."
            
        return result
        
    def run(self, query: str) -> str:
        return "Use structured input with 'repo_path', 'file_path', 'search_term', and optional 'search_type' and 'context_size'."

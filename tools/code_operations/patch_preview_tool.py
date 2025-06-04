from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import difflib
from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_ROOT")

class PatchPreviewInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="Relative path to file in the repository")
    modification_description: str = Field(..., description="Description of what changes to make")
    code_snippet: str = Field(default=None, description="Code snippet to insert (optional)")
    target_function: str = Field(default=None, description="Target function to modify (optional)")

class PatchPreviewTool(BaseTool):
    name: str = "patch_preview_tool"
    description: str = "Generates a patch preview for a file without applying changes"
    args_schema: Type[BaseModel] = PatchPreviewInput

    def _run(self, repo_name: str, file_path: str, modification_description: str, code_snippet: str = None, target_function: str = None) -> str:
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            if not os.path.isfile(full_path):
                return f"❌ File not found: {full_path}"
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                original_content = f.read()
            
            # Store original content in memory for reference
            # We'll use the session_state context in the chat application to store this
            patch_info = {
                "repo_name": repo_name,
                "file_path": file_path,
                "original_content": original_content,
                "modified_content": None,
                "description": modification_description
            }
            
            # Analyze the file and create a proposed modification based on the description
            modified_content = self._generate_modified_content(
                original_content, 
                modification_description, 
                code_snippet, 
                target_function
            )
            
            if modified_content == original_content:
                return f"⚠️ No changes were made based on the provided description: '{modification_description}'"
            
            # Store the modified content for later application
            patch_info["modified_content"] = modified_content
            
            # Generate a unified diff to show the changes
            diff = self._generate_diff(original_content, modified_content, file_path)
            
            # Return a preview that includes the patch info ID and the diff
            return f"""
            ## 📝 Patch Preview for {repo_name}/{file_path}

### Modification Description:
{modification_description}

### Changes Preview:
{diff}
"""
        
        except Exception as e:
            return f"❌ Error generating patch preview: {e}"

    def _generate_modified_content(self, original_content, modification_description, code_snippet=None, target_function=None):
        # This is a simplified version - you would implement the actual logic
        # based on the modification_description, code_snippet and target_function
        
        # If a specific code snippet was provided, try to insert it appropriately
        if code_snippet:
            if target_function:
                # Try to insert the code snippet into the specified function
                import re
                function_pattern = re.compile(r'function\s+' + re.escape(target_function) + r'\s*\([^)]*\)\s*{', re.DOTALL)
                match = function_pattern.search(original_content)
                
                if match:
                    # Find a good spot to insert the code (after the opening brace)
                    function_start = match.end()
                    insert_pos = original_content.find('\n', function_start)
                    if insert_pos > 0:
                        return original_content[:insert_pos] + f"\n\t{code_snippet}" + original_content[insert_pos:]
            
            # If no function specified or function not found, append to the end
            # (before closing PHP tag if present)
            if '?>' in original_content:
                return original_content.replace('?>', f"{code_snippet}\n?>")
            else:
                return original_content + f"\n\n{code_snippet}\n"
        
        # This is where you'd implement more sophisticated modification logic
        # based on the description and the file content
        return original_content  # Return original if no changes made

    def _generate_diff(self, original, modified, file_path):
        # Generate a unified diff
        original_lines = original.splitlines(True)
        modified_lines = modified.splitlines(True)
        
        diff = difflib.unified_diff(
            original_lines, 
            modified_lines,
            fromfile=f'a/{file_path}',
            tofile=f'b/{file_path}',
            n=3  # Context lines
        )
        
        return ''.join(diff)

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_name', 'file_path', and 'modification_description'."

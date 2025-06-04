from typing import Type, Literal
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import difflib
import subprocess
from tools.safety_validator import SafetyValidator
from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_ROOT")

class PatchInput(BaseModel):
    operation: Literal["preview", "apply"] = Field(..., description="Operation: preview or apply patch")
    repo_name: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="Relative path to file in the repository")
    modification_description: str = Field(default=None, description="Description of what changes to make (for preview)")
    modified_content: str = Field(default=None, description="New content to write to the file (for apply)")
    code_snippet: str = Field(default=None, description="Code snippet to insert (optional, for preview)")
    target_function: str = Field(default=None, description="Target function to modify (optional, for preview)")
    auto_branch: bool = Field(default=False, description="Automatically create AI branch if needed")

class PatchTool(BaseTool):
    name: str = "patch_tool"
    description: str = "Preview or apply changes to files with safety validation"
    args_schema: Type[BaseModel] = PatchInput

    def _run(self, operation: str, repo_name: str, file_path: str, 
             modification_description: str = None, modified_content: str = None,
             code_snippet: str = None, target_function: str = None,
             auto_branch: bool = False) -> str:
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            if not os.path.isfile(full_path):
                return f"❌ File not found: {full_path}"
            
            # For apply operations, check branch safety
            if operation == "apply":
                # Try auto-branching if requested
                if auto_branch:
                    success, message, branch_name = SafetyValidator.create_ai_branch_if_needed(repo_name)
                    if not success:
                        return message
                    
                # Validate branch safety
                is_valid, message = SafetyValidator.validate_branch_for_write_operation(repo_name)
                if not is_valid:
                    return f"{message}\nUse auto_branch=True to automatically create an AI branch."
                
                # Apply the patch
                return self._apply_patch(repo_name, file_path, modified_content)
            
            elif operation == "preview":
                # Preview doesn't need branch validation as it's read-only
                return self._preview_patch(repo_name, file_path, modification_description, 
                                          code_snippet, target_function)
            else:
                return f"❌ Unsupported operation: {operation}. Use 'preview' or 'apply'."
            
        except Exception as e:
            return f"❌ Error in patch operation: {e}"

    def _preview_patch(self, repo_name, file_path, modification_description, 
                      code_snippet=None, target_function=None):
        """Generate a preview of proposed changes"""
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                original_content = f.read()
            
            # Generate modified content based on description
            modified_content = self._generate_modified_content(
                original_content, 
                modification_description, 
                code_snippet, 
                target_function
            )
            
            if modified_content == original_content:
                return f"⚠️ No changes were made based on the provided description: '{modification_description}'"
            
            # Generate a unified diff to show the changes
            diff = self._generate_diff(original_content, modified_content, file_path)
            
            # Return a preview
            return f"""
## 📝 Patch Preview for {repo_name}/{file_path}

### Modification Description:
{modification_description}

### Changes Preview:
```diff
{diff}
```

To apply this patch, call the patch_tool with operation="apply" and the modified_content.
"""
        except Exception as e:
            return f"❌ Error generating patch preview: {e}"

    def _apply_patch(self, repo_name, file_path, modified_content):
        """Apply changes to the file"""
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            # Create backup
            backup_path = full_path + ".bak"
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                original_content = f.read()
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Generate diff for reporting
            diff = self._generate_diff(original_content, modified_content, file_path)
            
            # Write new content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return f"""
## ✅ Patch Applied to {repo_name}/{file_path}

### Changes Made:
```diff
{diff}
```

A backup was created at {file_path}.bak
"""
        except Exception as e:
            return f"❌ Error applying patch: {e}"

    def _generate_modified_content(self, original_content, modification_description, 
                                 code_snippet=None, target_function=None):
        """Generate modified content based on description and parameters"""
        # If specific code snippet provided, try to insert it
        if code_snippet:
            if target_function:
                # Try to insert code snippet into specified function
                import re
                function_pattern = re.compile(r'function\s+' + re.escape(target_function) + r'\s*\([^)]*\)\s*{', re.DOTALL)
                match = function_pattern.search(original_content)
                
                if match:
                    # Find good spot to insert (after opening brace)
                    function_start = match.end()
                    insert_pos = original_content.find('\n', function_start)
                    if insert_pos > 0:
                        return original_content[:insert_pos] + f"\n\t{code_snippet}" + original_content[insert_pos:]
            
            # If no function or not found, append to end (before closing PHP tag if present)
            if '?>' in original_content:
                return original_content.replace('?>', f"{code_snippet}\n?>")
            else:
                return original_content + f"\n\n{code_snippet}\n"
        
        # This is a simplified approach - in a real implementation, this would use
        # more sophisticated logic or even an LLM call to generate the modified content
        # based on the description
        return original_content  # Return original if no changes determined

    def _generate_diff(self, original, modified, file_path):
        """Generate a unified diff between original and modified content"""
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        diff = difflib.unified_diff(
            original_lines, 
            modified_lines,
            fromfile=f'a/{file_path}',
            tofile=f'b/{file_path}',
            lineterm='',
            n=3  # Context lines
        )
        
        return '\n'.join(diff)

    def run(self, query: str) -> str:
        return "Use structured input with 'operation', 'repo_name', 'file_path', and operation-specific parameters."

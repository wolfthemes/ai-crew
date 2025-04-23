from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os

REPO_ROOT = os.path.abspath("repos")

class PatchApplyInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="Relative path to file in the repository")
    modified_content: str = Field(..., description="New content to write to the file")

class PatchApplyTool(BaseTool):
    name: str = "patch_apply_tool"
    description: str = "Applies a patch by writing modified content to a file"
    args_schema: Type[BaseModel] = PatchApplyInput

    def _run(self, repo_name: str, file_path: str, modified_content: str) -> str:
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            if not os.path.isfile(full_path):
                return f"❌ File not found: {full_path}"
            
            # Backup the original file
            backup_path = full_path + ".bak"
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    original_content = f.read()
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
            except Exception as e:
                return f"❌ Failed to create backup before applying patch: {e}"
            
            # Write the modified content
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
            except Exception as e:
                # Try to restore from backup if write fails
                try:
                    with open(backup_path, 'r', encoding='utf-8', errors='replace') as f:
                        backup_content = f.read()
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(backup_content)
                except:
                    pass
                
                return f"❌ Failed to apply patch: {e}"
            
            return f"✅ Successfully applied patch to {repo_name}/{file_path}. A backup was created at {file_path}.bak"
            
        except Exception as e:
            return f"❌ Error applying patch: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_name', 'file_path', and 'modified_content'."
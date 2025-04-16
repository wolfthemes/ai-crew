from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import shutil

REPO_ROOT = os.path.abspath("repos")

class FileOperationsInput(BaseModel):
    source_repo: str = Field(..., description="Source repository name")
    source_path: str = Field(..., description="Relative path to source file in source repo")
    target_repo: str = Field(..., description="Target repository name")
    target_path: str = Field(..., description="Relative path where file should be copied in target repo")

class FileOperationsTool(BaseTool):
    name: str = "file_operations_tool"
    description: str = "Copies files between repositories"
    args_schema: Type[BaseModel] = FileOperationsInput

    def _run(self, source_repo: str, source_path: str, target_repo: str, target_path: str) -> str:
        try:
            # Build full paths
            source_full_path = os.path.join(REPO_ROOT, source_repo, source_path)
            target_full_path = os.path.join(REPO_ROOT, target_repo, target_path)
            
            # Check if source exists
            if not os.path.isfile(source_full_path):
                return f"❌ Source file not found: {source_full_path}"
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_full_path, target_full_path)
            
            return f"✅ Successfully copied {source_repo}/{source_path} to {target_repo}/{target_path}"
        
        except Exception as e:
            return f"❌ Error copying file: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'source_repo', 'source_path', 'target_repo', and 'target_path'."
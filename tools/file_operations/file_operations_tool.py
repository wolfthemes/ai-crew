from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import shutil
import subprocess
from dotenv import load_dotenv
load_dotenv()
REPO_ROOT = os.getenv("LOCAL_REPOS_ROOT")

class FileOperationsInput(BaseModel):
    source_repo: str = Field(..., description="Source repository name")
    source_path: str = Field(..., description="Relative path to source file in source repo")
    target_repo: str = Field(..., description="Target repository name")
    target_path: str = Field(..., description="Relative path where file should be copied in target repo")

class FileOperationsTool(BaseTool):
    name: str = "file_operations_tool"
    description: str = "Copies files between repositories with safety checks"
    args_schema: Type[BaseModel] = FileOperationsInput

    def _run(self, source_repo: str, source_path: str, target_repo: str, target_path: str) -> str:
        try:
            # Build full paths
            source_full_path = os.path.join(REPO_ROOT, source_repo, source_path)
            target_full_path = os.path.join(REPO_ROOT, target_repo, target_path)
            
            # Check if source exists
            if not os.path.isfile(source_full_path):
                return f"❌ Source file not found: {source_full_path}"
            
            # Safety check: Verify we're on an AI branch in target repo
            is_safe, message = self._verify_ai_branch(target_repo)
            if not is_safe:
                return message
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_full_path, target_full_path)
            
            return f"✅ Successfully copied {source_repo}/{source_path} to {target_repo}/{target_path}"
        
        except Exception as e:
            return f"❌ Error copying file: {e}"
    
    def _verify_ai_branch(self, repo_name):
        """Verify that we're on an AI branch in the target repo"""
        repo_path = os.path.join(REPO_ROOT, repo_name)
        if not os.path.exists(repo_path):
            return False, f"❌ Repository not found: {repo_path}"
        
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            branch_name = result.stdout.strip()
            
            # Check if branch name contains 'ai-' or '-ai'
            if not (branch_name.startswith('ai-') or '-ai' in branch_name):
                return False, f"⚠️ Safety restriction: Can only perform write operations on branches with 'ai-' or '-ai' in the name. Current branch: '{branch_name}'"
            
            return True, "Branch validation passed"
            
        except subprocess.CalledProcessError as e:
            return False, f"❌ Git error when checking branch: {e.stderr if hasattr(e, 'stderr') else str(e)}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def run(self, query: str) -> str:
        return "Use structured input with 'source_repo', 'source_path', 'target_repo', and 'target_path'."

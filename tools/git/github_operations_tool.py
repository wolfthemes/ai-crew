from typing import Type, Literal
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import subprocess
import re
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.path.abspath("repos")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class GitHubCloneInput(BaseModel):
    repo_name: str = Field(..., description="The name of the repository (e.g. vinylparadise)")
    owner: str = Field(default=GITHUB_USERNAME, description="The owner of the repository (user or org)")
    branch: str = Field(default="main", description="Branch to checkout")

class GitOperationInput(BaseModel):
    operation: Literal["commit", "branch", "checkout", "push", "pull", "pr"] = Field(
        ..., description="Git operation to perform"
    )
    repo_name: str = Field(..., description="Repository name")
    params: dict = Field(..., description="Operation-specific parameters")

class BranchValidationMixin:
    """Mixin to validate branch names for AI safety"""
    
    def is_ai_branch(self, branch_name):
        """Check if branch name contains 'ai-' or '-ai'"""
        return branch_name and (branch_name.startswith('ai-') or '-ai' in branch_name)
    
    def validate_branch_for_write_operation(self, branch_name):
        """Validate branch name for write operations"""
        if not self.is_ai_branch(branch_name):
            return False, f"⚠️ Safety restriction: Can only perform write operations on branches with 'ai-' or '-ai' in the name. '{branch_name}' is not allowed."
        return True, "Branch name validated for write operation."

class GitHubTool(BaseTool, BranchValidationMixin):
    name: str = "github_tool"
    description: str = "Clones a GitHub repo using env-based authentication"
    args_schema: Type[BaseModel] = GitHubCloneInput

    def _run(self, repo_name: str, owner: str = GITHUB_USERNAME, branch: str = "main") -> str:
        try:
            if not GITHUB_USERNAME or not GITHUB_TOKEN:
                return "GITHUB_USERNAME and/or GITHUB_TOKEN not set in environment."

            repo_url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}.git"
            clone_path = os.path.join(REPO_ROOT, repo_name)

            if os.path.exists(clone_path):
                return f"CLONE_STATUS: SKIPPED — Repo already exists at {clone_path}"

            os.makedirs(REPO_ROOT, exist_ok=True)

            # First attempt: clone with specified branch (default: main)
            try:
                subprocess.run(
                    ["git", "clone", "--branch", branch, "--single-branch", repo_url, repo_name],
                    cwd=REPO_ROOT,
                    check=True
                )
                return f"CLONE_STATUS: SUCCESS — Repo '{owner}/{repo_name}' cloned to {clone_path} on branch '{branch}'"
            except subprocess.CalledProcessError as e:
                if branch == "main":
                    # Retry with 'master' as fallback
                    try:
                        subprocess.run(
                            ["git", "clone", "--branch", "master", "--single-branch", repo_url, repo_name],
                            cwd=REPO_ROOT,
                            check=True
                        )
                        return f"CLONE_STATUS: SUCCESS — Repo '{owner}/{repo_name}' cloned to {clone_path} on fallback branch 'master'"
                    except subprocess.CalledProcessError as e2:
                        return f"CLONE_STATUS: FAILED — Tried 'main' and 'master'. Git error: {e2}"
                else:
                    return f"CLONE_STATUS: FAILED — Git error: {e}"

        except Exception as e:
            return f"CLONE_STATUS: FAILED — Error: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_name', optional 'owner', and 'branch'."

class GitOperationsTool(BaseTool, BranchValidationMixin):
    name: str = "git_operations_tool"
    description: str = "Performs git operations: commit, branch, checkout, push, pull, create PR"
    args_schema: Type[BaseModel] = GitOperationInput

    def _run(self, operation: str, repo_name: str, params: dict) -> str:
        repo_path = os.path.join(REPO_ROOT, repo_name)
        
        if not os.path.exists(repo_path):
            return f"❌ Repository not found: {repo_path}"
        
        try:
            # Get current branch for operations that need it
            if operation in ["commit", "push", "pull"]:
                current_branch = self._get_current_branch(repo_path)
                
                # For write operations, validate branch name
                if operation in ["commit", "push"]:
                    is_valid, message = self.validate_branch_for_write_operation(current_branch)
                    if not is_valid:
                        return message
            
            if operation == "commit":
                message = params.get("message", "Automated commit")
                files = params.get("files", ".")
                
                # Stage files
                subprocess.run(
                    ["git", "add", files],
                    cwd=repo_path,
                    check=True
                )
                
                # Commit
                subprocess.run(
                    ["git", "commit", "-m", message],
                    cwd=repo_path,
                    check=True
                )
                
                return f"✅ Successfully committed changes in {repo_name} with message: {message}"
                
            elif operation == "branch":
                branch_name = params.get("branch_name")
                if not branch_name:
                    return "❌ branch_name parameter is required"
                
                # Suggest AI branch name if not compliant
                if not self.is_ai_branch(branch_name):
                    ai_branch_name = f"ai-{branch_name}"
                    return f"⚠️ For safety, branch names should include 'ai-' or '-ai'. Suggested name: {ai_branch_name}"
                
                subprocess.run(
                    ["git", "branch", branch_name],
                    cwd=repo_path,
                    check=True
                )
                
                return f"✅ Successfully created branch {branch_name} in {repo_name}"
                
            elif operation == "checkout":
                branch_name = params.get("branch_name")
                if not branch_name:
                    return "❌ branch_name parameter is required"
                
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=repo_path,
                    check=True
                )
                
                return f"✅ Successfully checked out branch {branch_name} in {repo_name}"
                
            elif operation == "push":
                branch_name = params.get("branch_name", "current")
                remote = params.get("remote", "origin")
                
                if branch_name == "current":
                    branch_name = self._get_current_branch(repo_path)
                
                # Safety check for branch name
                is_valid, message = self.validate_branch_for_write_operation(branch_name)
                if not is_valid:
                    return message
                
                subprocess.run(
                    ["git", "push", remote, branch_name],
                    cwd=repo_path,
                    check=True,
                    env={**os.environ, "GIT_ASKPASS": "echo", "GIT_USERNAME": GITHUB_USERNAME, "GIT_PASSWORD": GITHUB_TOKEN}
                )
                
                return f"✅ Successfully pushed {branch_name} to {remote} in {repo_name}"
                
            elif operation == "pull":
                remote = params.get("remote", "origin")
                branch_name = params.get("branch_name", "current")
                
                if branch_name == "current":
                    branch_name = self._get_current_branch(repo_path)
                
                subprocess.run(
                    ["git", "pull", remote, branch_name],
                    cwd=repo_path,
                    check=True
                )
                
                return f"✅ Successfully pulled latest changes from {remote}/{branch_name} in {repo_name}"
                
            elif operation == "pr":
                base = params.get("base_branch", "main")
                head = params.get("head_branch")
                title = params.get("title")
                body = params.get("body", "")
                
                if not head or not title:
                    return "❌ head_branch and title parameters are required"
                
                # Safety check for head branch name
                is_valid, message = self.validate_branch_for_write_operation(head)
                if not is_valid:
                    return message
                
                # Create PR using GitHub CLI if installed
                try:
                    subprocess.run(
                        ["gh", "pr", "create", "--base", base, "--head", head, "--title", title, "--body", body],
                        cwd=repo_path,
                        check=True,
                        env={**os.environ, "GITHUB_TOKEN": GITHUB_TOKEN}
                    )
                    return f"✅ Successfully created PR from {head} to {base} in {repo_name}"
                except FileNotFoundError:
                    return "❌ GitHub CLI (gh) not found. Install it to create PRs."
                
            else:
                return f"❌ Unsupported git operation: {operation}"
                
        except subprocess.CalledProcessError as e:
            return f"❌ Git error: {e.stderr if hasattr(e, 'stderr') else str(e)}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _get_current_branch(self, repo_path):
        """Helper method to get current branch name"""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def run(self, query: str) -> str:
        return "Use structured input with 'operation', 'repo_name', and operation-specific 'params'."
from typing import Type, Literal
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_DIR")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class GitCommitInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    message: str = Field(..., description="Commit message")
    files: str = Field(".", description="Files to commit (. for all)")

class GitPRInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    base_branch: str = Field(default="main", description="Base branch (target)")
    head_branch: str = Field(..., description="Head branch (source with your changes)")
    title: str = Field(..., description="PR title")
    body: str = Field(default="", description="PR description")

class GitOperationsInput(BaseModel):
    operation: Literal["commit", "branch", "checkout", "push", "pull", "pr"] = Field(
        ..., description="Git operation to perform"
    )
    repo_name: str = Field(..., description="Repository name")
    params: dict = Field(..., description="Operation-specific parameters")

class GitOperationsTool(BaseTool):
    name: str = "git_operations_tool"
    description: str = "Performs git operations: commit, branch, checkout, push, pull, create PR"
    args_schema: Type[BaseModel] = GitOperationsInput

    def _run(self, operation: str, repo_name: str, params: dict) -> str:
        repo_path = os.path.join(REPO_ROOT, repo_name)
        
        if not os.path.exists(repo_path):
            return f"❌ Repository not found: {repo_path}"
        
        try:
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
                    # Get current branch name
                    result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        cwd=repo_path,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    branch_name = result.stdout.strip()
                
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
                    result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        cwd=repo_path,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    branch_name = result.stdout.strip()
                
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

    def run(self, query: str) -> str:
        return "Use structured input with 'operation', 'repo_name', and operation-specific 'params'."

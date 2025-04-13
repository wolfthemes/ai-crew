from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import subprocess

REPO_ROOT = os.path.abspath("repos")

class GitHubInput(BaseModel):
    repo_name: str = Field(..., description="The name of the repository (e.g. sample-plugin)")
    branch: str = Field(default="main", description="Branch to checkout")

class GitHubTool(BaseTool):
    name: str = "github_tool"
    description: str = "Clones a GitHub repo using env-based authentication"
    args_schema: Type[BaseModel] = GitHubInput

    def _run(self, repo_name: str, branch: str) -> str:
        try:
            username = os.getenv("GITHUB_USERNAME")
            token = os.getenv("GITHUB_TOKEN")

            if not username or not token:
                return "GITHUB_USERNAME and/or GITHUB_TOKEN not set in environment."

            repo_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
            clone_path = os.path.join(REPO_ROOT, repo_name)

            if os.path.exists(clone_path):
                return f"Repo already exists at {clone_path}"

            os.makedirs(REPO_ROOT, exist_ok=True)

            subprocess.run(
                ["git", "clone", "--branch", branch, "--single-branch", repo_url, repo_name],
                cwd=REPO_ROOT,
                check=True
            )

            return f"Repo '{repo_name}' cloned to {clone_path} on branch '{branch}'"

        except subprocess.CalledProcessError as e:
            return f"Git error: {e}"
        except Exception as e:
            return f"Error: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with repo_name and branch."

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.path.abspath("repos")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class GitHubInput(BaseModel):
    repo_name: str = Field(..., description="The name of the repository (e.g. vinylparadise)")
    owner: str = Field(default=GITHUB_USERNAME, description="The owner of the repository (user or org)")
    branch: str = Field(default="main", description="Branch to checkout")

class GitHubTool(BaseTool):
    name: str = "github_tool"
    description: str = "Clones a GitHub repo using env-based authentication"
    args_schema: Type[BaseModel] = GitHubInput

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

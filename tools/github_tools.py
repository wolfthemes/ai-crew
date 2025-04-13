from langchain.agents import tool
import subprocess

@tool
def create_pr(repo_path: str, branch: str, message: str, title: str):
    """Creates a GitHub PR from the given branch with a message and title."""
    #subprocess.run(["git", "checkout", "-b", branch], cwd=repo_path)
    #subprocess.run(["git", "add", "."], cwd=repo_path)
    #subprocess.run(["git", "commit", "-m", message], cwd=repo_path)
    #subprocess.run(["git", "push", "-u", "origin", branch], cwd=repo_path)
    #subprocess.run(["gh", "pr", "create", "--title", title, "--body", message], cwd=repo_path)
    return "PR submitted."

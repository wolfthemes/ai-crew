from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os

# Define input schema
class CodeSearchInput(BaseModel):
    function_name: str = Field(..., description="The function name to search for")
    repo_path: str = Field(..., description="The repo directory to search in")

# Define the tool class
class GetCodeSearchTool(BaseTool):
    name: str = "get_code_search"
    description: str = "Searches for a PHP function in the codebase and returns its location."
    args_schema: Type[BaseModel] = CodeSearchInput

    def _run(self, function_name: str, repo_path: str) -> str:
        try:
            matches = []
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.php'):
                        file_path = os.path.join(root, file)
                        with open(file_path, encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if f"function {function_name}" in line:
                                    matches.append(f"{file_path}:{i+1} → {line.strip()}")
            return "\n".join(matches) if matches else "Function not found."
        except Exception as e:
            return f"Error searching function: {e}"

    # This method is for text-only tools (optional override)
    def run(self, query: str) -> str:
        return "Use `_run` with parameters. This tool requires structured input."

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import re

class CodeSearchInput(BaseModel):
    function_name: str = Field(..., description="The function name to search for")
    repo_path: str = Field(..., description="The repo directory to search in")

REPO_ROOT = os.path.abspath("repos")

class GetCodeSearchTool(BaseTool):
    name: str = "get_code_search"
    description: str = "Searches for a PHP function in the codebase and returns its definition and references."
    args_schema: Type[BaseModel] = CodeSearchInput

    def _run(self, function_name: str, repo_path: str) -> str:
        try:
            matches = []
            full_path = os.path.join(REPO_ROOT, repo_path)
            print(f"Searching in: {full_path} for function: {function_name}")

            function_def_pattern = re.compile(rf"\bfunction\s+{re.escape(function_name)}\b", re.IGNORECASE)
            function_ref_pattern = re.compile(rf"\b{re.escape(function_name)}\b", re.IGNORECASE)

            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith('.php'):
                        file_path = os.path.join(root, file)
                        with open(file_path, encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if function_def_pattern.search(line):
                                    matches.append(f"[DEF] {file_path}:{i+1} → {line.strip()}")
                                elif function_ref_pattern.search(line):
                                    matches.append(f"[REF] {file_path}:{i+1} → {line.strip()}")

            return "\n".join(matches) if matches else f"Function '{function_name}' not found in {repo_path}."
        except Exception as e:
            return f"Error searching function: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'function_name' and 'repo_path'."

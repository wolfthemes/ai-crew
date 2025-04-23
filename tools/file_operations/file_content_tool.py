from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os

REPO_ROOT = os.path.abspath("repos")

class FileContentInput(BaseModel):
    repo_name: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="Relative path to the file in the repository")

class FileContentTool(BaseTool):
    name: str = "file_content_tool"
    description: str = "Retrieves the content of a file from a repository"
    args_schema: Type[BaseModel] = FileContentInput

    def _run(self, repo_name: str, file_path: str) -> str:
        try:
            full_path = os.path.join(REPO_ROOT, repo_name, file_path)
            
            if not os.path.isfile(full_path):
                return f"❌ File not found: {full_path}"
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return f"Content of {repo_name}/{file_path}:\n\n```\n{content}\n```"
        
        except Exception as e:
            return f"❌ Error retrieving file content: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_name' and 'file_path'."
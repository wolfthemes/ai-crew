
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.getenv("LOCAL_REPOS_ROOT")

# Input schema
class FixCodeInput(BaseModel):
    repo_path: str = Field(..., description="The name of the repo (inside 'repos/')")
    file_path: str = Field(..., description="Relative path to the file inside the repo")
    instruction: str = Field(..., description="Instruction for how to fix or improve the code")

# FixCodeTool definition
class FixCodeTool(BaseTool):
    name: str = "fix_code_tool"
    description: str = "Uses OpenAI to fix or improve the content of a PHP (or other) code file."
    args_schema: Type[BaseModel] = FixCodeInput

    def _run(self, repo_path: str, file_path: str, instruction: str) -> str:
        full_path = os.path.join(REPO_ROOT, repo_path, file_path)

        if not os.path.isfile(full_path):
            return f"❌ File not found: {full_path}"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                original_code = f.read()
        except Exception as e:
            return f"❌ Error reading file: {e}"

        prompt = f"""
You are a senior PHP developer (or general code assistant if the file isn't PHP).

A developer is asking you to review and fix the following file.

### INSTRUCTION
{instruction}

### FILE: {file_path}
```php
{original_code}
```

Please return the corrected, complete file below (with no comments or explanation).
"""

        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful senior code assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"❌ Error communicating with OpenAI API: {e}"

    def run(self, query: str) -> str:
        return "Use structured input with 'repo_path', 'file_path', and 'instruction'."

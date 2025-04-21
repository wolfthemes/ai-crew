from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import date
import os

class MarkdownSaveInput(BaseModel):
    content: str = Field(..., description="The Markdown-formatted report content to save")
    path: str = Field(default=None, description="Optional file path to save the report")
    title: str = Field(default=None, description="Optional title for the report (for filename)")

class SaveToMarkdown(BaseTool):
    name: str = "save_to_markdown"
    description: str = "Saves a EUR/USD market report to a Markdown file"
    args_schema: Type[BaseModel] = MarkdownSaveInput
    
    # Add default path as a property
    default_path: Optional[str] = None
    
    def __init__(self, default_path=None):
        super().__init__()
        self.default_path = default_path
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, content: str, path: str = None, title: str = None) -> str:
        """Save the content to a markdown file"""
        # Use provided path, default path, or generate one
        if path:
            save_path = path
        elif self.default_path:
            save_path = self.default_path
        else:
            today = date.today().isoformat()
            filename = f"EUR_USD_Report_{today}.md"
            if title:
                # Clean title for filename use
                clean_title = "".join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in title)
                clean_title = clean_title.replace(' ', '_')
                filename = f"{clean_title}_{today}.md"
            
            # Make sure the reports directory exists
            os.makedirs("reports", exist_ok=True)
            save_path = os.path.join("reports", filename)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"MARKDOWN_SAVE_STATUS: SUCCESS — Report saved to {save_path}"
        except Exception as e:
            return f"MARKDOWN_SAVE_STATUS: FAILED — {e}"
    
    def run(self, query: str) -> str:
        return "Use structured input with `content`, optional `path`, and `title`."
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from notion_client import Client
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

class NotionPostInput(BaseModel):
    content: str = Field(..., description="The Markdown-formatted report content to post")
    title: str = Field(default=None, description="Optional title for the Notion entry (defaults to date)")
    date_str: str = Field(default=None, description="Optional date string in YYYY-MM-DD format")

class PostToNotion(BaseTool):
    name: str = "post_to_notion"
    description: str = "Posts a weekly EUR/USD report to a Notion database"
    args_schema: Type[BaseModel] = NotionPostInput
    
    # Add these as proper model fields
    notion: Optional[Client] = None
    database_id: Optional[str] = None

    def __init__(self):
        super().__init__()  # Required in some BaseTool setups
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("NOTION_MARKET_REPORTS_DB_KEY")

    class Config:
        arbitrary_types_allowed = True  # This allows the Client object to be stored

    def _run(self, content: str, title: str = None, date_str: str = None) -> str:
        today = date.today().isoformat() if not date_str else date_str
        title_text = title or f"EUR/USD Weekly Report – {today}"

        try:
            self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": title_text}}]},
                    "Date": {"date": {"start": today}},
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": content}
                                }
                            ]
                        }
                    }
                ]
            )
            return f"NOTION_POST_STATUS: SUCCESS — Report posted to Notion on {today}"
        except Exception as e:
            return f"NOTION_POST_STATUS: FAILED — {e}"

    def run(self, query: str) -> str:
        return "Use structured input with `content`, optional `title`, and `date_str`."
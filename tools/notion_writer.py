from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from notion_client import Client
from datetime import date
import os
import re
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
        try:
            self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
            self.database_id = os.getenv("NOTION_MARKET_REPORTS_DB_KEY")
            if not self.notion or not self.database_id:
                print("⚠️ Notion API key or database ID not found in environment variables")
        except Exception as e:
            print(f"⚠️ Failed to initialize Notion client: {e}")
            self.notion = None
            self.database_id = None

    class Config:
        arbitrary_types_allowed = True  # This allows the Client object to be stored
    
    def _markdown_to_notion_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Convert markdown content to Notion blocks format
        
        This is a simplified conversion that handles:
        - Headers (# to ######)
        - Paragraphs
        - Bullet lists
        - Numbered lists
        - Bold and italic text (limited support)
        """
        blocks = []
        current_list_items = []
        current_list_type = None
        
        # Split content into lines
        lines = markdown_content.split('\n')
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                # If we're in a list, add the list and reset
                if current_list_items:
                    if current_list_type == "bulleted":
                        blocks.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": current_list_items[0]["bulleted_list_item"]
                        })
                    elif current_list_type == "numbered":
                        blocks.append({
                            "object": "block",
                            "type": "numbered_list_item",
                            "numbered_list_item": current_list_items[0]["numbered_list_item"]
                        })
                    current_list_items = []
                    current_list_type = None
                continue
            
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # Determine header level
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                
                # Map to Notion header types
                header_type = f"heading_{level}"
                
                blocks.append({
                    "object": "block",
                    "type": header_type,
                    header_type: {
                        "rich_text": [{"type": "text", "text": {"content": header_text}}],
                        "color": "default"
                    }
                })
                continue
            
            # Check for bullet lists
            bullet_match = re.match(r'^\s*[-*+]\s+(.+)$', line)
            if bullet_match:
                list_text = bullet_match.group(1).strip()
                
                # If we're switching list types, add the previous list
                if current_list_type and current_list_type != "bulleted":
                    # Add the previous list
                    for item in current_list_items:
                        blocks.append(item)
                    current_list_items = []
                
                current_list_type = "bulleted"
                current_list_items.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": list_text}}],
                        "color": "default"
                    }
                })
                continue
            
            # Check for numbered lists
            numbered_match = re.match(r'^\s*(\d+)\.?\s+(.+)$', line)
            if numbered_match:
                list_text = numbered_match.group(2).strip()
                
                # If we're switching list types, add the previous list
                if current_list_type and current_list_type != "numbered":
                    # Add the previous list
                    for item in current_list_items:
                        blocks.append(item)
                    current_list_items = []
                
                current_list_type = "numbered"
                current_list_items.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": list_text}}],
                        "color": "default"
                    }
                })
                continue
            
            # If we're in a list and the line is not a list item, add the list and reset
            if current_list_items:
                # Add all list items
                for item in current_list_items:
                    blocks.append(item)
                current_list_items = []
                current_list_type = None
            
            # Default to paragraph
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}],
                    "color": "default"
                }
            })
        
        # Add any remaining list items
        if current_list_items:
            for item in current_list_items:
                blocks.append(item)
        
        return blocks

    def _run(self, content: str, title: str = None, date_str: str = None) -> str:
        # Check if Notion client is initialized
        if not self.notion or not self.database_id:
            return "NOTION_POST_STATUS: FAILED — Notion client not properly initialized"
        
        today = date.today().isoformat() if not date_str else date_str
        title_text = title or f"EUR/USD Weekly Report – {today}"
        
        try:
            # Convert markdown to Notion blocks
            blocks = self._markdown_to_notion_blocks(content)
            
            # Create the page with the blocks
            self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": title_text}}]},
                    "Date": {"date": {"start": today}},
                },
                children=blocks
            )
            
            return f"NOTION_POST_STATUS: SUCCESS — Report posted to Notion on {today}"
        except Exception as e:
            return f"NOTION_POST_STATUS: FAILED — {str(e)}"

    def run(self, query: str) -> str:
        return "Use structured input with `content`, optional `title`, and `date_str`."
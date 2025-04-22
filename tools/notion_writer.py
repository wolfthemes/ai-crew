import markdown2
from bs4 import BeautifulSoup
from typing import Type, Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field, ConfigDict
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
    notion: Optional[Client] = Field(default=None, exclude=True)
    database_id: Optional[str] = Field(default=None, exclude=True)
    
    # Add configuration for arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self):
        super().__init__()
        
        try:
            notion_api_key = os.getenv("NOTION_API_KEY")
            database_id = os.getenv("NOTION_MARKET_REPORTS_DB_KEY")
            
            if not notion_api_key or not database_id:
                print("⚠️ Notion API key or database ID not found in environment variables")
                self.notion = None
                self.database_id = None
            else:
                self.notion = Client(auth=notion_api_key)
                self.database_id = database_id
        except Exception as e:
            print(f"⚠️ Failed to initialize Notion client: {e}")
            self.notion = None
            self.database_id = None

    def html_to_notion_blocks(self, soup) -> List[Dict[str, Any]]:
        """Convert HTML elements to Notion blocks."""
        blocks = []
        
        # Process all top-level elements
        for element in soup.children:
            if element.name is None:
                # Skip empty text nodes
                continue
                
            # Handle headings (h1 to h6)
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                header_type = f"heading_{level}"
                blocks.append({
                    "object": "block",
                    "type": header_type,
                    header_type: {
                        "rich_text": [{"type": "text", "text": {"content": element.get_text()}}],
                        "color": "default"
                    }
                })
                
            # Handle paragraphs
            elif element.name == 'p':
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": element.get_text()}}],
                        "color": "default"
                    }
                })
                
            # Handle unordered lists
            elif element.name == 'ul':
                for li in element.find_all('li', recursive=False):
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": li.get_text()}}],
                            "color": "default"
                        }
                    })
                    
            # Handle ordered lists
            elif element.name == 'ol':
                for li in element.find_all('li', recursive=False):
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": li.get_text()}}],
                            "color": "default"
                        }
                    })
                    
            # Handle blockquotes
            elif element.name == 'blockquote':
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"type": "text", "text": {"content": element.get_text()}}],
                        "color": "default"
                    }
                })
                
            # Handle code blocks
            elif element.name == 'pre':
                code = element.find('code')
                if code:
                    language = "plain text"
                    # Try to extract language from class (e.g., "language-python")
                    if code.get('class'):
                        for cls in code.get('class'):
                            if cls.startswith('language-'):
                                language = cls[9:]
                                break
                                
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": language,
                            "rich_text": [{"type": "text", "text": {"content": code.get_text()}}]
                        }
                    })
                else:
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": "plain text",
                            "rich_text": [{"type": "text", "text": {"content": element.get_text()}}]
                        }
                    })
                    
            # Handle tables
            elif element.name == 'table':
                rows = []
                # Get all rows
                table_rows = element.find_all('tr', recursive=False)
                if table_rows:
                    # Determine table width from the first row
                    first_row = table_rows[0]
                    cells = first_row.find_all(['th', 'td'], recursive=False)
                    table_width = len(cells)
                    
                    # Process all rows
                    for row in table_rows:
                        cells = row.find_all(['th', 'td'], recursive=False)
                        # Ensure consistent number of cells
                        cell_list = []
                        for i in range(table_width):
                            if i < len(cells) and cells[i]:
                                cell_text = cells[i].get_text()
                            else:
                                cell_text = ""  # Empty cell for padding
                            
                            cell_list.append([{
                                "type": "text", 
                                "text": {"content": cell_text}
                            }])
                            
                        rows.append({
                            "type": "table_row",
                            "table_row": {
                                "cells": cell_list
                            }
                        })
                    
                    # Add the table block
                    blocks.append({
                        "object": "block",
                        "type": "table",
                        "table": {
                            "table_width": table_width,
                            "has_column_header": True,  # Assume first row is header
                            "has_row_header": False,
                            "children": rows
                        }
                    })
                    
            # Handle horizontal rules
            elif element.name == 'hr':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
                
            # Handle any other elements as paragraphs
            elif element.name:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": element.get_text()}}],
                        "color": "default"
                    }
                })
                
        return blocks

    def _run(self, content: str, title: str = None, date_str: str = None) -> str:
        # Check if Notion client is initialized
        if not self.notion:
            return "NOTION_POST_STATUS: FAILED — Notion client not properly initialized"
        
        today = date.today().isoformat() if not date_str else date_str
        title_text = title or f"EUR/USD Weekly Report – {today}"
        
        try:
            print(f"Converting markdown to HTML...")
            
            # Convert Markdown to HTML
            html = markdown2.markdown(
                content,
                extras=["tables", "fenced-code-blocks", "code-friendly"]
            )
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Convert HTML to Notion blocks
            blocks = self.html_to_notion_blocks(soup)
            
            # Split blocks into chunks of 100 (Notion API limit)
            block_chunks = [blocks[i:i+100] for i in range(0, len(blocks), 100)]
            
            print(f"Report will be posted in {len(block_chunks)} chunks ({len(blocks)} total blocks)")
            
            # Create the page with the first chunk of blocks
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                icon= {
                    "type": "emoji",
                    "emoji": "🏛️"
                },
                properties={
                    "Name": {"title": [{"text": {"content": title_text}}]},
                    "Date": {"date": {"start": today}},
                },
                children=block_chunks[0] if block_chunks else []  # First chunk only
            )
            
            page_id = response["id"]
            print(f"Created initial page with ID: {page_id}")
            
            # If there are more chunks, append them
            for i, chunk in enumerate(block_chunks[1:], 1):
                print(f"Appending chunk {i+1}/{len(block_chunks)}...")
                self.notion.blocks.children.append(
                    block_id=page_id,
                    children=chunk
                )
            
            return f"NOTION_POST_STATUS: SUCCESS — Report posted to Notion on {today}"
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return f"NOTION_POST_STATUS: FAILED — {str(e)}"

    def run(self, query: str) -> str:
        # This is the method that CrewAI will call when using the tool directly
        try:
            # For direct tool usage without structured input, extract content
            content = query
            title = None
            date_str = None
            
            # Try to extract title from first line if it starts with # 
            lines = content.split('\n')
            if lines and lines[0].startswith('# '):
                title = lines[0][2:].strip()
            
            return self._run(content=content, title=title, date_str=date_str)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return f"NOTION_POST_STATUS: FAILED — {str(e)}"
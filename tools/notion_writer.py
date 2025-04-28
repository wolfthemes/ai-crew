import markdown2
from bs4 import BeautifulSoup
from typing import Type, Optional, List, Dict, Any
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
    period: str = Field(default="Weekly", description="Report period type: 'Daily' or 'Weekly'")

class PostToNotion(BaseTool):
    name: str = "post_to_notion"
    description: str = "Posts a weekly EUR/USD report to a Notion database"
    args_schema: Type[BaseModel] = NotionPostInput
    
    # Add these as proper model fields
    notion: Optional[Client] = Field(default=None, exclude=True)
    database_id: Optional[str] = Field(default=None, exclude=True)
    
    # Add configuration for arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def extract_tables_from_markdown(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Extract tables directly from markdown text in case the HTML conversion didn't work.
        Returns a list of Notion blocks for each detected table.
        """
        table_blocks = []
        
        # Split the markdown into lines
        lines = markdown_text.split('\n')
        
        # Define regex pattern for markdown table rows
        header_pattern = re.compile(r'^\s*\|(.+)\|\s*$')
        separator_pattern = re.compile(r'^\s*\|([\s\-:|]+)\|\s*$')
        
        i = 0
        while i < len(lines):
            # Look for a potential table header
            header_match = header_pattern.match(lines[i]) if i < len(lines) else None
            
            # If we found a header, check if the next line is a separator
            if header_match and i + 1 < len(lines):
                separator_match = separator_pattern.match(lines[i + 1])
                
                if separator_match:
                    print(f"Found markdown table at line {i}")
                    # We found a table! Process it
                    header_cells = self._split_table_row(header_match.group(1))
                    table_width = len(header_cells)
                    rows = []
                    
                    # Add header row
                    header_row = {
                        "type": "table_row",
                        "table_row": {
                            "cells": [[{"type": "text", "text": {"content": cell.strip()}}] for cell in header_cells]
                        }
                    }
                    rows.append(header_row)
                    
                    # Process data rows
                    row_index = i + 2  # Start after the separator line
                    while row_index < len(lines):
                        row_match = header_pattern.match(lines[row_index])
                        if not row_match:
                            break  # End of table
                        
                        data_cells = self._split_table_row(row_match.group(1))
                        # Pad or truncate cells to match table_width
                        while len(data_cells) < table_width:
                            data_cells.append("")
                        if len(data_cells) > table_width:
                            data_cells = data_cells[:table_width]
                        
                        data_row = {
                            "type": "table_row",
                            "table_row": {
                                "cells": [[{"type": "text", "text": {"content": cell.strip()}}] for cell in data_cells]
                            }
                        }
                        rows.append(data_row)
                        row_index += 1
                    
                    # Create the table block
                    table_block = {
                        "object": "block",
                        "type": "table",
                        "table": {
                            "table_width": table_width,
                            "has_column_header": True,
                            "has_row_header": False,
                            "children": rows
                        }
                    }
                    table_blocks.append(table_block)
                    
                    # Skip ahead to after this table
                    i = row_index
                    continue
            
            i += 1
        
        print(f"Extracted {len(table_blocks)} tables directly from markdown")
        return table_blocks
    
    def _split_table_row(self, row: str) -> List[str]:
        """
        Split a markdown table row into cells, handling escaped pipes.
        """
        # Split by pipe character, but not if it's escaped with backslash
        cells = []
        current_cell = ""
        escape_next = False
        
        for char in row:
            if escape_next:
                current_cell += char
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '|':
                cells.append(current_cell)
                current_cell = ""
            else:
                current_cell += char
        
        # Add the last cell if not empty
        if current_cell:
            cells.append(current_cell)
        
        return cells

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
        
        # Find all tables in the document first, regardless of nesting
        all_tables = soup.find_all('table')
        print(f"Found {len(all_tables)} tables in the HTML")
        
        # Process all top-level elements
        for element in soup.body.children if soup.body else soup.children:
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
                #print(f"Processing table element: {element}")
                rows = []
                # Get all rows, including those within thead, tbody, tfoot
                table_rows = []
                
                # Check for thead/tbody/tfoot sections
                thead = element.find('thead')
                tbody = element.find('tbody')
                tfoot = element.find('tfoot')
                
                # Get rows from thead if it exists
                if thead:
                    thead_rows = thead.find_all('tr')
                    table_rows.extend(thead_rows)
                    print(f"Found {len(thead_rows)} rows in thead")
                
                # Get rows from tbody if it exists
                if tbody:
                    tbody_rows = tbody.find_all('tr')
                    table_rows.extend(tbody_rows)
                    print(f"Found {len(tbody_rows)} rows in tbody")
                
                # Get rows from tfoot if it exists
                if tfoot:
                    tfoot_rows = tfoot.find_all('tr')
                    table_rows.extend(tfoot_rows)
                    print(f"Found {len(tfoot_rows)} rows in tfoot")
                
                # If no structured sections, get rows directly
                if not table_rows:
                    table_rows = element.find_all('tr')
                    print(f"Found {len(table_rows)} direct rows in table")
                
                if table_rows:
                    # Determine table width from the first row
                    first_row = table_rows[0]
                    cells = first_row.find_all(['th', 'td'])
                    table_width = len(cells)
                    print(f"Table width: {table_width}")
                    
                                            # Process all rows
                    for row in table_rows:
                        cells = row.find_all(['th', 'td'])
                        # Ensure consistent number of cells
                        cell_list = []
                        for i in range(table_width):
                            if i < len(cells) and cells[i]:
                                cell_text = cells[i].get_text().strip()
                                # Check if the original text contains bold or other formatting
                                original_html = str(cells[i])
                                is_bold = '<strong>' in original_html or '<b>' in original_html
                            else:
                                cell_text = ""  # Empty cell for padding
                                is_bold = False
                            
                            # Create text with appropriate formatting
                            text_obj = {
                                "type": "text",
                                "text": {"content": cell_text}
                            }
                            
                            # Add bold annotation if needed
                            if is_bold:
                                text_obj["annotations"] = {"bold": True}
                            
                            cell_list.append([text_obj])
                            
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
                    print(f"Added table with {len(rows)} rows to blocks")
                    
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

    def _run(self, content: str, title: str = None, date_str: str = None, period: str = None) -> str:
        # Check if Notion client is initialized
        if not self.notion:
            return "NOTION_POST_STATUS: FAILED — Notion client not properly initialized"
        
        # Ensure period is capitalized and valid
        period = period.capitalize()
        if period not in ["Daily", "Weekly"]:
            print(f"Warning: Invalid period '{period}', defaulting to 'Weekly'")
            period = "Weekly"
        
        today = date.today().isoformat() if not date_str else date_str
        title_text = title or f"EUR/USD {period} Report – {today}"
        
        try:
            print(f"Converting markdown to HTML...")
            
            # Convert Markdown to HTML with enhanced table support
            html = markdown2.markdown(
                content,
                extras=[
                    "tables",
                    "fenced-code-blocks", 
                    "code-friendly",
                    "cuddled-lists",
                    "footnotes",
                    "header-ids",
                    "html-classes",
                    "markdown-in-html",
                    "strike",
                    "target-blank-links"
                ]
            )
            
            # Output HTML to a file for debugging
            debug_html_path = "debug/debug_markdown_output.html"
            with open(debug_html_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved HTML output to {debug_html_path} for debugging")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Output pretty-printed HTML structure for debugging
            debug_structure_path = "debug/debug_html_structure.txt"
            with open(debug_structure_path, "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print(f"Saved pretty HTML structure to {debug_structure_path} for debugging")
            
            # Check if we need to manually handle tables from the markdown
            # Some markdown tables may not be properly converted to HTML tables
            manual_table_blocks = self.extract_tables_from_markdown(content)
            
            # Convert HTML to Notion blocks
            blocks = self.html_to_notion_blocks(soup)
            
            # Add any manually detected tables
            if manual_table_blocks:
                print(f"Adding {len(manual_table_blocks)} manually detected tables")
                blocks.extend(manual_table_blocks)
            
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
                    "Period": {"select": {"name": period}}
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
            
            return f"NOTION_POST_STATUS: SUCCESS — {period} Report posted to Notion on {today}"
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
            period = "Weekly"  # Default period
            
            # Try to extract title from first line if it starts with # 
            lines = content.split('\n')
            if lines and lines[0].startswith('# '):
                title = lines[0][2:].strip()

                # Try to determine period from title
                if "daily" in title.lower():
                    period = "Daily"
                elif "weekly" in title.lower():
                    period = "Weekly"
            
            return self._run(content=content, title=title, date_str=date_str, period=period)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return f"NOTION_POST_STATUS: FAILED — {str(e)}"
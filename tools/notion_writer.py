# Python solution for Notion markdown conversion
# pip install markdown2 python-dotenv notion-client pydantic crewai crewai-tools bs4

import os
import re
import json
from typing import Type, Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from crewai.tools import BaseTool
from notion_client import Client
from dotenv import load_dotenv
import markdown2
from bs4 import BeautifulSoup

load_dotenv()

# Valid Notion code block languages
VALID_NOTION_LANGUAGES = {
    "abap", "agda", "arduino", "ascii art", "assembly", "bash", "basic", "bnf", 
    "c", "c#", "c++", "clojure", "coffeescript", "coq", "css", "dart", "dhall", 
    "diff", "docker", "ebnf", "elixir", "elm", "erlang", "f#", "flow", "fortran", 
    "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "hcl", "html", "idris", 
    "java", "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", 
    "livescript", "llvm ir", "lua", "makefile", "markdown", "markup", "matlab", 
    "mathematica", "mermaid", "nix", "notion formula", "objective-c", "ocaml", 
    "pascal", "perl", "php", "plain text", "powershell", "prolog", "protobuf", 
    "purescript", "python", "r", "racket", "reason", "ruby", "rust", "sass", 
    "scala", "scheme", "scss", "shell", "smalltalk", "solidity", "sql", "swift", 
    "toml", "typescript", "vb.net", "verilog", "vhdl", "visual basic", 
    "webassembly", "xml", "yaml", "java/c/c++/c#", "notionscript"
}

# Mapping of common language names to valid Notion language values
LANGUAGE_MAPPING = {
    "js": "javascript",
    "py": "python",
    "ts": "typescript",
    "rb": "ruby",
    "cs": "c#",
    "cpp": "c++",
    "plain_text": "plain text",
    "plaintext": "plain text",
    "txt": "plain text",
    "sh": "bash",
    "zsh": "bash",
    "md": "markdown",
    "yml": "yaml",
    "htm": "html",
    "jsx": "javascript",
    "tsx": "typescript",
    "fs": "f#",
    "pl": "perl",
    "ps": "powershell",
    "ps1": "powershell",
    "bat": "powershell",
    "cmd": "powershell",
    "hs": "haskell",
    "kt": "kotlin",
    "m": "matlab",
    "mm": "objective-c",
    "objc": "objective-c",
    "rs": "rust",
    "scss": "sass",
    "tex": "latex",
    "vb": "visual basic"
}

class NotionPostInput(BaseModel):
    content: str = Field(..., description="The Markdown-formatted report content to post")
    title: str = Field(default=None, description="Optional title for the Notion entry (defaults to date)")
    date_str: str = Field(default=None, description="Optional date string in YYYY-MM-DD format")
    period: str = Field(default="Weekly", description="Report period type: 'Daily' or 'Weekly'")

class PostToNotion(BaseTool):
    name: str = "post_to_notion"
    description: str = "Posts a EUR/USD report to a Notion database"
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

    def extract_tables_from_markdown(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Extract tables directly from markdown text.
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

    def get_valid_language(self, language: str) -> str:
        """Convert language identifier to a valid Notion language."""
        language = language.strip().lower()
        
        # Check if it's already a valid Notion language
        if language in VALID_NOTION_LANGUAGES:
            return language
            
        # Check if it's in our mapping
        if language in LANGUAGE_MAPPING:
            return LANGUAGE_MAPPING[language]
            
        # Default to "plain text" if not found
        return "plain text"

    def process_html_for_styling(self, content: str) -> List[Dict[str, Any]]:
        """Process HTML content to extract styled text for Notion rich text."""
        soup = BeautifulSoup(content, 'html.parser')
        rich_text_list = []
        
        # Process each element for styling
        for element in soup.descendants:
            if element.name is None and element.string and element.string.strip():
                # Plain text
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": element.string.strip()}
                })
            elif element.name == 'strong' or element.name == 'b':
                # Bold text
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": element.get_text().strip()},
                    "annotations": {"bold": True}
                })
            elif element.name == 'em' or element.name == 'i':
                # Italic text
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": element.get_text().strip()},
                    "annotations": {"italic": True}
                })
            elif element.name == 'code':
                # Inline code
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": element.get_text().strip()},
                    "annotations": {"code": True}
                })
            elif element.name == 'a':
                # Link
                rich_text_list.append({
                    "type": "text",
                    "text": {
                        "content": element.get_text().strip(),
                        "link": {"url": element.get('href', '#')}
                    }
                })
            elif element.name == 's' or element.name == 'del':
                # Strikethrough
                rich_text_list.append({
                    "type": "text",
                    "text": {"content": element.get_text().strip()},
                    "annotations": {"strikethrough": True}
                })
        
        # Merge consecutive text nodes with the same styling to avoid fragmentation
        if rich_text_list:
            return rich_text_list
        
        # Default to plain text if no styled elements found
        return [{"type": "text", "text": {"content": content}}]

    def markdown_to_notion_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Convert markdown to Notion blocks with enhanced formatting."""
        # Convert markdown to HTML with extended features
        html = markdown2.markdown(
            markdown_content,
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
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        blocks = []
        
        # Extract all elements
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'ul', 'ol', 'li', 'blockquote', 'hr']):
            # Handle headings
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = min(int(element.name[1]), 3)  # Notion supports h1, h2, h3 only
                header_type = f"heading_{level}"
                
                # Extract text with styling
                rich_text = self.process_html_for_styling(str(element))
                
                blocks.append({
                    "object": "block",
                    "type": header_type,
                    header_type: {
                        "rich_text": rich_text,
                        "color": "default"
                    }
                })
                
            # Handle paragraphs
            elif element.name == 'p' and not element.parent.name in ['li', 'blockquote']:
                # Extract text with styling
                rich_text = self.process_html_for_styling(str(element))
                
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text,
                        "color": "default"
                    }
                })
                
            # Handle code blocks
            elif element.name == 'pre':
                code_element = element.find('code')
                if code_element:
                    # Get language if specified in class
                    language = "plain text"  # Default language
                    if code_element.get('class'):
                        for class_name in code_element.get('class'):
                            if class_name.startswith('language-'):
                                language = class_name[9:]
                                break
                    
                    # Convert to a valid Notion language
                    valid_language = self.get_valid_language(language)
                    
                    # Extract code content
                    code_content = code_element.get_text()
                    
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": code_content}}],
                            "language": valid_language
                        }
                    })
                    
            # Handle lists
            elif element.name == 'li':
                # Determine list type (bulleted or numbered)
                parent = element.parent
                list_type = "bulleted_list_item" if parent.name == 'ul' else "numbered_list_item"
                
                # Extract text with styling
                rich_text = self.process_html_for_styling(str(element))
                
                blocks.append({
                    "object": "block",
                    "type": list_type,
                    list_type: {
                        "rich_text": rich_text,
                        "color": "default"
                    }
                })
                
            # Handle blockquotes
            elif element.name == 'blockquote':
                # Extract text with styling
                rich_text = self.process_html_for_styling(str(element))
                
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": rich_text,
                        "color": "default"
                    }
                })
                
            # Handle horizontal rules
            elif element.name == 'hr':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
        
        # Extract tables (they're usually not properly handled by BeautifulSoup)
        table_blocks = self.extract_tables_from_markdown(markdown_content)
        blocks.extend(table_blocks)
        
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
            print(f"Converting markdown to Notion blocks...")
            
            # Convert markdown to Notion blocks
            blocks = self.markdown_to_notion_blocks(content)
            
            # Create debug directory if it doesn't exist
            os.makedirs("debug", exist_ok=True)
            
            # Output blocks for debugging
            debug_blocks_path = "debug/debug_notion_blocks.json"
            with open(debug_blocks_path, "w", encoding="utf-8") as f:
                json.dump(blocks, f, indent=2)
            print(f"Saved Notion blocks to {debug_blocks_path} for debugging")
            
            # Validate all blocks before sending
            for block in blocks:
                block_type = block.get("type")
                
                # Ensure code blocks have valid language
                if block_type == "code" and "code" in block:
                    if "language" in block["code"]:
                        # Make sure language is a valid Notion language
                        block["code"]["language"] = self.get_valid_language(block["code"]["language"])
                    else:
                        # Default to plain text if language is missing
                        block["code"]["language"] = "plain text"
                        
                    # Ensure rich_text is provided
                    if "rich_text" not in block["code"] or not block["code"]["rich_text"]:
                        block["code"]["rich_text"] = [{"type": "text", "text": {"content": ""}}]
            
            # Split blocks into chunks of 100 (Notion API limit)
            block_chunks = [blocks[i:i+100] for i in range(0, len(blocks), 100)]
            
            print(f"Report will be posted in {len(block_chunks)} chunks ({len(blocks)} total blocks)")
            
            # Set emoji icon based on period
            if period.lower() == "daily":
                emoji_icon = "📅"
            elif period.lower() == "weekly":
                emoji_icon = "🏛️"
            else:
                emoji_icon = "🗓️"  # Default or fallback

            # Create the page with the first chunk of blocks
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                icon= {
                    "type": "emoji",
                    "emoji": emoji_icon
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

# Usage example:
# 
# from notion_writer import PostToNotion
#
# # Initialize the tool
# notion_tool = PostToNotion()
#
# # Sample markdown content
# markdown_content = """
# # EUR/USD Weekly Report - 2025-05-05
#
# ## Market Summary
#
# The EUR/USD pair showed significant volatility this week, closing at 1.0842.
#
# ## Key Technical Levels
#
# | Level | Type | Price |
# |-------|------|-------|
# | R2 | Resistance | 1.0925 |
# | R1 | Resistance | 1.0880 |
# | PP | Pivot Point | 1.0842 |
# | S1 | Support | 1.0810 |
# | S2 | Support | 1.0775 |
#
# ## Analysis
#
# The pair continues to trade in a consolidation pattern between 1.0775 and 1.0925.
# """
#
# # Post to Notion
# result = notion_tool.run(markdown_content)
# print(result)
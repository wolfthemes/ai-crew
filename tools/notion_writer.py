# Enhanced NotionWriter with improved formatting
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
from bs4 import BeautifulSoup, Tag, NavigableString

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
                            "cells": [[{"type": "text", "text": {"content": cell.strip()}, "annotations": {"bold": True}}] for cell in header_cells]
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

    def _parse_styling(self, element) -> Dict[str, Any]:
        """Recursively parse HTML elements to extract text with styling."""
        if isinstance(element, NavigableString):
            return {"type": "text", "text": {"content": str(element).strip()}}
            
        if isinstance(element, Tag):
            text = element.get_text().strip()
            if not text:
                return None
                
            result = {"type": "text", "text": {"content": text}}
            
            # Add styling annotations as needed
            if element.name in ['strong', 'b']:
                result["annotations"] = {"bold": True}
            elif element.name in ['em', 'i']:
                result["annotations"] = {"italic": True}
            elif element.name == 'code':
                result["annotations"] = {"code": True}
            elif element.name in ['s', 'del']:
                result["annotations"] = {"strikethrough": True}
            elif element.name == 'a' and element.get('href'):
                result["text"]["link"] = {"url": element.get('href')}
                
            return result
            
        return None

    def process_html_for_styling(self, element) -> List[Dict[str, Any]]:
        """Process HTML content to extract styled text for Notion rich text."""
        if isinstance(element, str):
            soup = BeautifulSoup(element, 'html.parser')
            element = soup
            
        rich_text_list = []
        
        if isinstance(element, Tag):
            # Process direct text content
            for content in element.contents:
                if isinstance(content, NavigableString) and content.strip():
                    rich_text_list.append({"type": "text", "text": {"content": content.strip()}})
                elif isinstance(content, Tag):
                    if content.name in ['strong', 'b']:
                        rich_text_list.append({
                            "type": "text", 
                            "text": {"content": content.get_text().strip()},
                            "annotations": {"bold": True}
                        })
                    elif content.name in ['em', 'i']:
                        rich_text_list.append({
                            "type": "text", 
                            "text": {"content": content.get_text().strip()},
                            "annotations": {"italic": True}
                        })
                    elif content.name == 'code':
                        rich_text_list.append({
                            "type": "text", 
                            "text": {"content": content.get_text().strip()},
                            "annotations": {"code": True}
                        })
                    elif content.name in ['s', 'del']:
                        rich_text_list.append({
                            "type": "text", 
                            "text": {"content": content.get_text().strip()},
                            "annotations": {"strikethrough": True}
                        })
                    elif content.name == 'a':
                        rich_text_list.append({
                            "type": "text",
                            "text": {
                                "content": content.get_text().strip(),
                                "link": {"url": content.get('href', '#')}
                            }
                        })
                    else:
                        # Recursively process nested elements
                        nested_text = self.process_html_for_styling(content)
                        if nested_text:
                            rich_text_list.extend(nested_text)
        
        # Filter out empty items and ensure proper formatting
        rich_text_list = [item for item in rich_text_list if item.get("text", {}).get("content", "").strip()]
        
        # If no rich text was found, return plain text
        if not rich_text_list and isinstance(element, Tag):
            text = element.get_text().strip()
            if text:
                return [{"type": "text", "text": {"content": text}}]
                
        return rich_text_list

    def extract_markdown_lists(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Directly extract lists from markdown text to ensure proper nesting."""
        list_blocks = []
        lines = markdown_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for bulleted list items
            bullet_match = re.match(r'^(\s*)(?:[-*+])\s+(.+)$', lines[i])
            if bullet_match:
                indent_level = len(bullet_match.group(1))
                content = bullet_match.group(2).strip()
                
                # Create the list item
                list_blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": content}}],
                        "color": "default"
                    }
                })
                i += 1
                continue
                
            # Check for numbered list items
            number_match = re.match(r'^(\s*)(\d+)\.?\s+(.+)$', lines[i])
            if number_match:
                indent_level = len(number_match.group(1))
                content = number_match.group(3).strip()
                
                # Create the list item
                list_blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": content}}],
                        "color": "default"
                    }
                })
                i += 1
                continue
                
            i += 1
            
        return list_blocks

    def markdown_to_notion_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Convert markdown to Notion blocks with enhanced formatting."""
        blocks = []
        
        # First directly extract any tables
        table_blocks = self.extract_tables_from_markdown(markdown_content)
        
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
        
        # Create debug directory if it doesn't exist
        os.makedirs("debug", exist_ok=True)
        
        # Output HTML for debugging
        with open("debug/debug_html_output.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Dictionary to track section hierarchy for better nesting
        section_hierarchy = {}
        current_section = None
        current_level = 0
        
        # Process all top-level elements
        for element in soup.contents:
            if not isinstance(element, Tag):
                continue
                
            # Handle headings - reset section hierarchy
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                level = min(level, 3)  # Notion only supports h1-h3
                header_type = f"heading_{level}"
                
                # Extract text with styling
                rich_text = self.process_html_for_styling(element)
                
                # Create heading block
                blocks.append({
                    "object": "block",
                    "type": header_type,
                    header_type: {
                        "rich_text": rich_text,
                        "color": "default"
                    }
                })
                
                # Update section tracking
                current_section = element.get_text().strip()
                current_level = level
                for l in range(level, 7):
                    section_hierarchy[l] = None
                section_hierarchy[level] = current_section
            
            # Handle paragraphs
            elif element.name == 'p':
                # Extract text with styling
                rich_text = self.process_html_for_styling(element)
                
                if rich_text:
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
            
            # Handle lists (both ul and ol)
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=False):
                    list_type = "bulleted_list_item" if element.name == 'ul' else "numbered_list_item"
                    
                    # Process styled text in the list item
                    rich_text = self.process_html_for_styling(li)
                    
                    blocks.append({
                        "object": "block",
                        "type": list_type,
                        list_type: {
                            "rich_text": rich_text,
                            "color": "default"
                        }
                    })
                    
                    # Process any nested lists
                    nested_ul = li.find('ul')
                    nested_ol = li.find('ol')
                    
                    if nested_ul:
                        for nested_li in nested_ul.find_all('li', recursive=False):
                            rich_text = self.process_html_for_styling(nested_li)
                            blocks.append({
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": rich_text,
                                    "color": "default"
                                }
                            })
                            
                    if nested_ol:
                        for nested_li in nested_ol.find_all('li', recursive=False):
                            rich_text = self.process_html_for_styling(nested_li)
                            blocks.append({
                                "object": "block",
                                "type": "numbered_list_item",
                                "numbered_list_item": {
                                    "rich_text": rich_text,
                                    "color": "default"
                                }
                            })
            
            # Handle blockquotes
            elif element.name == 'blockquote':
                rich_text = self.process_html_for_styling(element)
                
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
        
        # Add tables at their appropriate positions
        blocks.extend(table_blocks)
        
        # Sort blocks to ensure tables appear in the right place
        # This is a simplified approach - for complex documents, 
        # you might need a more sophisticated ordering mechanism
        
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
                        
                # Ensure all rich text arrays are properly formatted
                for key in ["paragraph", "heading_1", "heading_2", "heading_3", 
                            "bulleted_list_item", "numbered_list_item", "quote"]:
                    if block_type == key and key in block:
                        if "rich_text" not in block[key] or not block[key]["rich_text"]:
                            block[key]["rich_text"] = [{"type": "text", "text": {"content": ""}}]
                        
                        # Make sure all rich_text items have proper structure
                        for i, text_item in enumerate(block[key]["rich_text"]):
                            if "text" not in text_item:
                                text_item["text"] = {"content": ""}
                            if "content" not in text_item["text"]:
                                text_item["text"]["content"] = ""
            
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
import os
import requests
import markdown2
from dotenv import load_dotenv

# Load Notion API key from .env
load_dotenv()
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('1db94b059238809892e5edcb7995b5d3')
MD_FILE_PATH = 'data/reports/weekly/eurusd_weekly_report_2025-05-05.md'

# Notion API endpoints
NOTION_API_URL = 'https://api.notion.com/v1/pages'
NOTION_VERSION = '2022-06-28'

# Helper: Convert markdown to Notion blocks (basic version)
def markdown_to_notion_blocks(md_content):
    """
    Converts markdown content to a list of Notion blocks.
    This is a minimal implementation. For advanced features, use a dedicated library[1][7].
    """
    html = markdown2.markdown(md_content)
    lines = html.split('\n')
    blocks = []
    for line in lines:
        if not line.strip():
            continue
        # Simple heading detection
        if line.startswith('<h1>'):
            text = line.replace('<h1>', '').replace('</h1>', '')
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
        elif line.startswith('<h2>'):
            text = line.replace('<h2>', '').replace('</h2>', '')
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
        else:
            # Strip HTML tags for basic paragraphs
            import re
            text = re.sub('<[^<]+?>', '', line)
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
    return blocks

# Helper: Chunk blocks into batches of 100 (Notion API limit)[6][7]
def chunk_blocks(blocks, chunk_size=100):
    for i in range(0, len(blocks), chunk_size):
        yield blocks[i:i + chunk_size]

# Read markdown file
with open(MD_FILE_PATH, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to Notion blocks
blocks = markdown_to_notion_blocks(md_content)

# Prepare the page properties (customize as needed)
properties = {
    "Name": {
        "title": [
            {
                "text": {
                    "content": "EURUSD Weekly Report 2025-05-05"
                }
            }
        ]
    }
}

# Create the Notion page with the first chunk of blocks
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def create_notion_page(parent_database_id, properties, children):
    data = {
        "parent": {"database_id": parent_database_id},
        "properties": properties,
        "children": children
    }
    response = requests.post(NOTION_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def append_blocks_to_page(page_id, blocks):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    data = {"children": blocks}
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Upload in chunks
chunks = list(chunk_blocks(blocks, 100))
first_chunk = chunks[0]
page = create_notion_page(DATABASE_ID, properties, first_chunk)
page_id = page['id']

# Upload remaining chunks
for chunk in chunks[1:]:
    append_blocks_to_page(page_id, chunk)

print("Upload complete!")


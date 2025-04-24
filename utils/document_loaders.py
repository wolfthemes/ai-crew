import os
import json
import sqlite3
from langchain_core.documents import Document
from utils.helpers import parse_json_file, clean_html_to_text

DATA_FOLDER = "data"

def format_documents(raw_data, source, content_key="content", title_key="title", url_key="url", 
                   additional_metadata=None):
    """
    Create documents with consistent metadata structure.
    additional_metadata is an optional dict of additional fields to include
    """
    documents = []
    for item in raw_data:
        content = item.get(content_key)
        if not content:
            continue
            
        # Process content based on source type
        page_content = clean_html_to_text(content) if source == "kb_article" else content.strip()
        
        # Create base metadata
        metadata = {
            "title": item.get(title_key, "Untitled"),
            "url": item.get(url_key, ""),
            "source": source,
        }
        
        # Add source-specific metadata if provided
        if additional_metadata:
            for key, value in additional_metadata.items():
                if isinstance(value, str) and value.startswith("item."):
                    # This is a reference to an item field
                    field_name = value.split(".", 1)[1]
                    metadata[key] = item.get(field_name, "")
                else:
                    # This is a static value
                    metadata[key] = value
        
        documents.append(Document(
            page_content=page_content,
            metadata=metadata
        ))
    return documents

def load_theme_meta():
    data = parse_json_file(os.path.join(DATA_FOLDER, "data/themes/theme_metadata/theme_catalog.json"))
    documents = []
    for slug, meta in data.items():
        builder = meta.get("builder", "Unknown")
        name = meta.get("name", slug)
        documents.append(Document(
            page_content=f"{name} uses the {builder} page builder.",
            metadata={
                "title": f"{name} Builder Info",
                "slug": slug,
                "builder": builder,
                "theme": name,  # Add theme name for consistency
                "version": meta.get("version"),
                "updated": meta.get("updated"),
                "url": meta.get("url"),
                "demourl": meta.get("demourl"),
                "shortlink": meta.get("shortlink"),
                "category": meta.get("category"),
                "source": "theme_info"
            }
        ))
    return documents

def load_kb_articles():
    return format_documents(
        parse_json_file(os.path.join(DATA_FOLDER, "crawled/kb_articles.json")), 
        "kb_article",
        additional_metadata={
            # Extract any theme or builder mentions if possible
            "theme": "",  # No default extraction
            "builder": ""  # No default extraction
        }
    )

def load_theme_docs():
    return format_documents(
        parse_json_file(os.path.join(DATA_FOLDER, "crawled/theme_docs.json")), 
        "theme_doc",
        additional_metadata={
            "slug": "item.slug",  # Reference to the item's slug field
            "theme": ""  # This could be derived from slug if needed
        }
    )

def load_common_issues():
    data = parse_json_file(os.path.join(DATA_FOLDER, "static/common_issues.json"))
    return [
        Document(
            page_content = (
                f"COMMON TITLE: {item['title']}\n"
                f"CUSTOMER ISSUE: {item['issue']}\n"
                f"SOLUTION: {item['solution']}"
            ),
            metadata={
                "title": item["title"],
                "source": "common_issue",
                "issue": item["issue"],
                "solution": item["solution"],
                "plugin": item.get("plugin", []),
                "builder": item.get("builder", ""),
                "theme": item.get("theme", ""),
                "human_validation": item.get("human_validation", False),
                "customization_summary": item.get("customization_summary", "")
            }
        )
        for item in data
    ]

def load_reference_tickets():
    data = parse_json_file(os.path.join(DATA_FOLDER, "static/reference_tickets.json"))
    return [
        Document(
            page_content = (
                f"REFERENCE TITLE: {item['title']}\n"
                f"CUSTOMER ISSUE: {item['issue']}\n"
                f"SOLUTION: {item['solution']}"
            ),
            metadata={
                "title": item["title"],
                "source": "reference_ticket",
                "issue": item["issue"],
                "solution": item["solution"],
                "plugin": item.get("plugin", []),
                "builder": item.get("builder", ""),
                "theme": item.get("theme", ""),
                "human_validation": item.get("human_validation", False)
            }
        )
        for item in data
    ]

def load_closed_tickets_from_db(db_path: str) -> list[Document]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id, created_at, theme, builder, formatted_text_thread, full_thread_summary FROM closed_tickets")
    rows = cursor.fetchall()
    conn.close()

    docs = []
    for row in rows:
        ticket_id, created_at, theme, builder, thread, summary = row
        metadata = {
            "ticket_id": ticket_id,
            "created_at": created_at,
            "theme": theme,
            "builder": builder,
            "summary": summary,
            "source": "support_ticket",
            "title": f"Ticket #{ticket_id}: {summary[:30]}..."
        }
        docs.append(Document(page_content=thread, metadata=metadata))

    return docs

# --- Load static prompts ---

def load_support_agent_backstory(path="prompts/support_agent_backstory.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()
    
def load_support_agent_instructions(path="prompts/support_agent_instructions.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()
    
def load_reformulate_agent_instructions(path="prompts/reformulate_agent_instructions.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()
    
def load_guidelines(path="prompts/support_task_guidelines.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()
    
def load_dev_agent_backstory(path="prompts/dev_agent_backstory.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()

import os
import json
from langchain_core.documents import Document
from utils.helpers import parse_json_file, clean_html_to_text

DATA_FOLDER = "data"

def format_documents(raw_data, source, content_key="content", title_key="title", url_key="url"):
    documents = []
    for item in raw_data:
        content = item.get(content_key)
        if not content:
            continue
        page_content = clean_html_to_text(content) if source == "kb_article" else content.strip()
        documents.append(Document(
            page_content=page_content,
            metadata={
                "title": item.get(title_key, "Untitled"),
                "url": item.get(url_key, ""),
                "source": source,
                **({"slug": item.get("slug")} if source == "theme_doc" else {})
            }
        ))
    return documents

def load_theme_meta():
    data = parse_json_file(os.path.join(DATA_FOLDER, "crawled/theme_info.json"))
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
    return format_documents(parse_json_file(os.path.join(DATA_FOLDER, "crawled/kb_articles.json")), "kb_article")

def load_theme_docs():
    return format_documents(parse_json_file(os.path.join(DATA_FOLDER, "crawled/theme_docs.json")), "theme_doc")

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
                "source": item.get("source", "common_issue"),
                "solution": item["solution"],
            }
        )
        for item in data
    ]

def load_reference_tickets():
    data = parse_json_file(os.path.join(DATA_FOLDER, "static/reference_tickets.json"))
    return [
        Document(
            page_content = (
                f"COMMON TITLE: {item['title']}\n"
                f"CUSTOMER ISSUE: {item['issue']}\n"
                f"SOLUTION: {item['solution']}"
            ),
            metadata={
                "title": item["title"],
                "source": item.get("source", "reference_ticket"),
                "solution": item["solution"],
            }
        )
        for item in data
    ]

def load_closed_tickets():
    """Load closed support tickets from a JSON file."""
    path = os.path.join(DATA_FOLDER, "crawled/closed_tickets.json")
    data = parse_json_file(path)

    if isinstance(data, dict) and "closed-tickets" in data:
        data = data["closed-tickets"]

    documents = []
    for t in data:
        if not isinstance(t, dict) or not t.get("ticket_comments"):
            continue

        text_blocks = []
        for c in t["ticket_comments"]:
            comment = clean_html_to_text(c.get("comment", ""))
            if comment:
                is_private = c.get("private") == "1"
                prefix = f"[PRIVATE] " if is_private else ""
                text_blocks.append(f"{prefix}{c.get('commenter_name', 'User')}:\n{comment}")
        conversation = "\n\n---\n\n".join(text_blocks)
        if conversation.strip():
            theme = "Unknown Theme"
            envato_str = t.get("envato_verified_string")
            if isinstance(envato_str, str):
                try:
                    theme_data = json.loads(envato_str)
                    theme = theme_data.get("item_name", theme)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON in envato_verified_string for ticket {t.get('ticket_id', 'unknown')}")
                except Exception as e:
                    print(f"⚠️ Error parsing envato_verified_string for ticket {t.get('ticket_id', 'unknown')}: {e}")

            documents.append(Document(
                page_content=conversation.strip(),
                metadata={
                    "title": t.get("ticket_title", "Untitled Ticket"),
                    "url": t.get("related_url", ""),
                    "ticket_id": t.get("ticket_id"),
                    "theme": theme,
                    "source": "support_ticket"
                }
            ))
    return documents

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
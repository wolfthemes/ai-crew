
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
    data = parse_json_file(os.path.join(DATA_FOLDER, "theme_info.json"))
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
    return format_documents(parse_json_file(os.path.join(DATA_FOLDER, "kb_articles.json")), "kb_article")

def load_theme_docs():
    return format_documents(parse_json_file(os.path.join(DATA_FOLDER, "theme_docs.json")), "theme_doc")

def load_common_issues():
    data = parse_json_file(os.path.join(DATA_FOLDER, "common_issues.json"))
    return [
        Document(
            page_content = (
                f"ISSUE TITLE: {item['title']}\n"
                f"RELATED QUESTION: {item['customer_message']}\n"
                f"SOLUTION: {item['expected_response']}"
            ),
            metadata={
                "title": item["title"],
                "issue_type": item.get("issue_type", "common_issue"),
                "expected_response": item["expected_response"],
                "source": "common_issue",
                "human_validation": item.get("human_validation", False),
                "customization_summary": item.get("customization_summary", "")
            }
        )
        for item in data
    ]


def load_theme_notes():
    data = parse_json_file(os.path.join(DATA_FOLDER, "theme_notes.json"))
    return [
        Document(
            page_content=item["note"],
            metadata={
                "title": item["title"],
                "theme": item.get("theme"),
                "version": item.get("version"),
                "source": "theme_note"
            }
        ) for item in data
    ]

def load_ticket_examples():
    data = parse_json_file(os.path.join(DATA_FOLDER, "ticket_examples.json"))
    return [
        Document(
            page_content=f"CUSTOMER MESSAGE: {item.get('customer_message', '')} EXPECTED RESPONSE: {item.get('expected_response', '')}",
            metadata={
                "title": item.get("title", "Untitled"),
                "issue_type": item.get("issue_type", "unknown"),
                "source": "ticket_example"
            }
        ) for item in data
    ]

def load_closed_tickets():
    """Load closed support tickets from a JSON file."""
    path = os.path.join(DATA_FOLDER, "closed_tickets.json")
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

def load_backstory(path="data/support_agent_backstory.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()
    
def load_guidelines(path="data/support_task_guidelines.md"):
    with open(path, encoding="utf-8") as f:
        return f.read()
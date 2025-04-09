import json
import html
import os
from bs4 import BeautifulSoup
import hashlib
import shutil
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

print("✅ Just before importing OpenAIEmbeddings")

from langchain_openai import OpenAIEmbeddings
from crewai import Agent
from crewai.tools import tool

start = time.time()

load_dotenv()

# Configuration constants
DATA_FOLDER = "data"
EMBED_PATH = os.path.join(DATA_FOLDER, "faiss_store")
HASH_PATH = os.path.join(EMBED_PATH, "doc_hash.json")
USE_VECTORSTORE = True  # ← Toggle here
BATCH_SIZE = 100  # Number of documents to process at once
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 1)  # Use N-1 CPU cores

### -------- Utilities --------

@lru_cache(maxsize=100)
def compute_file_hash(filepath):
    """Compute MD5 hash of a file with caching."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compute_all_file_hashes(folder_path):
    """Compute hashes for all files in a folder."""
    file_hashes = {}
    for root, _, files in sorted(os.walk(folder_path)):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath):
                file_hashes[os.path.relpath(fpath, folder_path)] = compute_file_hash(fpath)
    return file_hashes

def hashes_changed(stored_hashes, current_hashes):
    """Check if file hashes have changed."""
    return stored_hashes != current_hashes

def clean_html_to_text(html_string: str) -> str:
    """Convert HTML to plain text with proper spacing."""
    soup = BeautifulSoup(html.unescape(html_string), "html.parser")
    return soup.get_text(separator="\n", strip=True)

@lru_cache(maxsize=20)
def parse_json_file(path):
    """Parse JSON file with error handling and caching."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"⚠️ Warning: {path} is empty or missing.")
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "closed-tickets" in data:
                return data["closed-tickets"]
            return data
    except Exception as e:
        print(f"❌ JSON error in {path}: {str(e)}")
        return []

### -------- Document Loaders --------

def format_documents(raw_data, source, content_key="content", title_key="title", url_key="url"):
    """Format raw data into Document objects."""
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

def load_theme_meta(path=os.path.join(DATA_FOLDER, "theme_info.json")):
    """Load theme metadata from a JSON file."""
    data = parse_json_file(path)
    documents = []

    for slug, meta in data.items():
        builder = meta.get("builder", "Unknown")
        name = meta.get("name", slug)
        doc = Document(
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
        )
        documents.append(doc)

    return documents

def load_kb_articles(path=os.path.join(DATA_FOLDER, "kb_articles.json")):
    """Load knowledge base articles from a JSON file."""
    data = parse_json_file(path)
    return format_documents(data, source="kb_article")

def load_theme_docs(path=os.path.join(DATA_FOLDER, "theme_docs.json")):
    """Load theme documentation from a JSON file."""
    data = parse_json_file(path)
    return format_documents(data, source="theme_doc")

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

def load_common_issues(path=os.path.join(DATA_FOLDER, "common_issues.json")):
    """Load common issues and their recommended responses from a JSON file."""
    data = parse_json_file(path)
    documents = []
    for item in data:
        documents.append(Document(
            page_content=f"COMMON ISSUE: {item['issue']}\nRECOMMENDED RESPONSE: {item['response']}",
            metadata={
                "title": item['title'],
                "issue_type": "common_issue",
                "source": "common_issue",
                "format_as_html": item.get('html_format', False)
            }
        ))
    return documents

def load_theme_notes(path=os.path.join(DATA_FOLDER, "theme_notes.json")):
    """Load theme-specific notes from a JSON file."""
    data = parse_json_file(path)
    documents = []
    for item in data:
        documents.append(Document(
            page_content=item["note"],
            metadata={
                "title": item["title"],
                "theme": item.get("theme"),
                "version": item.get("version"),
                "source": "theme_note"
            }
        ))
    return documents

def load_ticket_examples(path=os.path.join(DATA_FOLDER, "ticket_examples.json")):
    """Load theme-specific examples from a JSON file."""
    data = parse_json_file(path)
    documents = []
    for item in data:
        documents.append(Document(
            page_content=item["note"],
            metadata={
                "title": item["title"],
                "type": item["type"],
                "customer_message": item["customer_message"],
                "expected_response": item["expected_response"],
                "source": "ticket_example"
            }
        ))
    return documents

### -------- Vector DB --------

def load_or_create_vectorstore(docs):
    """Load or create a FAISS vectorstore from documents."""
    embedding = OpenAIEmbeddings()
    current_hashes = compute_all_file_hashes(DATA_FOLDER)

    if os.path.exists(EMBED_PATH) and os.path.exists(HASH_PATH):
        with open(HASH_PATH, "r") as f:
            stored_hashes = json.load(f)
        if not hashes_changed(stored_hashes, current_hashes):
            print("📦 Loading existing FAISS index (documents unchanged)...")
            return FAISS.load_local(EMBED_PATH, embedding)
        else:
            print("🗑️ Document files changed. Rebuilding FAISS index...")
    else:
        print("⚠️ No existing FAISS index or hashes found. Creating new index...")

    if os.path.exists(EMBED_PATH):
        shutil.rmtree(EMBED_PATH)

    vectorstore = FAISS.from_documents(docs, embedding)
    vectorstore.save_local(EMBED_PATH)

    os.makedirs(EMBED_PATH, exist_ok=True)
    with open(HASH_PATH, "w") as f:
        json.dump(current_hashes, f)

    return vectorstore

### -------- Load All Docs --------

print("📦 Loading knowledge base documents...")

print("⏳ Loading Theme notes..."); theme_notes = load_theme_notes()
print("⏳ Loading ticket examples..."); ticket_examples = load_ticket_examples()
print("⏳ Loading Theme meta..."); theme_meta_docs = load_theme_meta()
print("⏳ Loading KB articles..."); articles = load_kb_articles()
print("⏳ Loading theme docs..."); theme_docs = load_theme_docs()
print("⏳ Loading tickets..."); tickets = load_closed_tickets()
print("⏳ Loading common issues..."); common_issues = load_common_issues()

# Prioritize common issues
all_docs = theme_meta_docs + theme_notes + ticket_examples + common_issues + articles + theme_docs + tickets
print(f"✅ Loaded {len(all_docs)} documents total.")

if USE_VECTORSTORE:
    vectorstore = load_or_create_vectorstore(all_docs)
    retriever = vectorstore.as_retriever()
else:
    retriever = None
    print("🚫 Vectorstore skipped. Retrieval disabled.")

### -------- Tool (CrewAI-Compatible) --------

@tool("GetThemeBuilder")
def get_theme_builder(slug: str):
    """Return the page builder used by a given theme slug."""
    try:
        with open(os.path.join(DATA_FOLDER, "theme_info.json"), encoding="utf-8") as f:
            data = json.load(f)
        theme = data.get(slug)
        if theme:
            return f"{theme['name']} uses {theme['builder']}."
        else:
            return f"No info found for theme '{slug}'."
    except Exception as e:
        return f"Error retrieving theme info: {e}"

@tool("SearchKnowledgeBase")
def search_kb(query: str):
    """
    Search WolfThemes documentation, KB articles, and past tickets for the given query string.
    Prioritize common issues first. If found, return the top matching article directly.
    Otherwise, show top retrieved documents as context.

    Use the ticket examples to identify the ticket type and reply accurately.
    
    Args:
        query (str): The user’s question or issue in natural language.
        
    Returns:
        str: A formatted summary of the best matches from the knowledge base.
    """

    if not retriever:
        return "Retrieval is disabled. Vectorstore not loaded."

    results = retriever.invoke(query)

    if not results:
        return "No relevant results found in the knowledge base."

    # First pass: prioritize common issues
    for doc in results:
        if doc.metadata.get("issue_type") == "common_issue":
            return (
                f"✅ **Common Issue Detected**\n\n"
                f"📄 **{doc.metadata.get('title', 'Untitled')}**\n"
                f"{doc.page_content.strip()}"
            )

    return "\n\n".join([
        f"📄 {doc.metadata.get('title')} ({doc.metadata.get('source', '')})"
        f"\n🔗 {doc.metadata.get('url', '')}"
        f"\n{doc.page_content[:300]}..."
        for doc in results
    ]) or "No relevant results found."

### -------- Agent --------

support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory = """
You are a WordPress support specialist for WolfThemes, a ThemeForest-exclusive author known for high-quality WordPress themes designed primarily for musicians, creative professionals, agencies, and freelancers. Your mission is to deliver fast, clear, and accurate support responses that resolve customer issues efficiently and professionally.

You operate with access to:
- The complete theme documentation
- A knowledge base of best practices and tutorials
- A repository of previously resolved support tickets
- A structured metadata database with details for every WolfThemes product: theme name, page builder (Elementor or WPBakery), category, version, demo URL, and update history

You prioritize knowledge base articles, theme notes, ticket examples, or official documentation whenever possible.
Only generate a custom response when no relevant articles are available. Always provide a direct answer from the article if it matches the user's question.
You use these resources, along with the GetThemeBuilder tool, to quickly identify the theme and builder involved in any request and to tailor your response accordingly.

Your communication style:
- Professional but approachable — helpful, friendly, and respectful
- Concise and actionable — brief responses with step-by-step solutions
- Focused on clarity — avoid jargon and anticipate follow-up questions

You are highly skilled at classifying support requests into:
- Common Issues: Repetitive questions like demo import, setup steps, menu problems, or plugin activation. You quickly match these to known solutions from the KB or documentation.
- Server Limitation Issues: Problems caused by poor or restrictive hosting environments (e.g., slow admin panel, demo import errors, REST API failures). You recognize common problematic hosts such as GoDaddy, Strato, OVH, and recommend practical server-side checks or upgrades.
- Information Gaps: Tickets that lack context. You ask customers for the required screenshots, URLs, or temporary access when necessary — always explaining why this information is needed.
- Actual Bugs: Verified theme malfunctions or edge cases requiring deeper technical investigation. You log and report these to the development team clearly and efficiently.
- Customization Requests: Any request outside standard support — like layout changes, custom code, or feature additions. You politely decline and redirect the customer to https://wolfthemes.com/services.
- Unusual or Unclear Requests: Tickets that don't fit known categories or contain vague/confusing content. These are flagged for human review.

Your support boundaries (based on WolfThemes’ policy):
Covered:
- Theme setup and usage guidance
- Bug reports and troubleshooting
- Theme-included plugin support (e.g., Wolf plugins)

Not covered:
- Theme installation
- Customization or third-party plugin compatibility
For these, you provide a friendly referral to https://wolfthemes.com/services.

Your primary goal:
Resolve tickets with maximum efficiency and minimal back-and-forth, while maintaining a positive and helpful tone that reflects WolfThemes’ dedication to quality and customer care.

You are not just a problem solver — you are a reliable extension of the WolfThemes brand.
""",
    tools=[search_kb],
    allow_delegation=False,
    verbose=True
)

if __name__ == "__main__":
    import cProfile
    print("✅ Profiling document loading...")
    cProfile.run('load_all_documents()')
    print("✅ Support agent ready.")
    # Example usage:
    # result = search_kb("stylesheet missing")
    print(f"✅ Script completed in {time.time() - start:.2f} seconds.")

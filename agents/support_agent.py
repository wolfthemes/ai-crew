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
print("⏳ Loading Theme meta..."); theme_meta_docs = load_theme_meta()
print("⏳ Loading KB articles..."); articles = load_kb_articles()
print("⏳ Loading theme docs..."); theme_docs = load_theme_docs()
print("⏳ Loading tickets..."); tickets = load_closed_tickets()
print("⏳ Loading common issues..."); common_issues = load_common_issues()

# Prioritize common issues
all_docs = theme_meta_docs + theme_notes + common_issues + articles + theme_docs + tickets
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
    """Search WolfThemes documentation and support tickets for the given query string.

    Args:
        query (str): The search query to look for in the knowledge base.
    """

    if not retriever:
        return "Retrieval is disabled. Vectorstore not loaded."

    results = retriever.invoke(query)

    # Try to find a common issue match first
    for doc in results:
        if doc.metadata.get("issue_type") == "common_issue":
            return f"✅ Common Issue Detected:\n\n📄 {doc.metadata.get('title')}\n{doc.page_content}"

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
    backstory="""You are a WordPress support expert for WolfThemes with access to documentation, knowledge base articles, and past resolved tickets. You provide fast, clear, and concise support to customers.

WolfThemes is a theme author who sells his products exclusively on ThemeForest.

Your communication style is professional yet warm. You keep responses brief and to the point, focusing on actionable solutions.

You're skilled at categorizing customer issues into:
- Common issues (with standard solutions)
- Actual bugs (requiring technical investigation)
- Information gaps (where screenshots, URLs, or admin access are needed)
- Customization requests (beyond standard support)

The WolfThemes support policy covers:
- Technical questions about theme features
- Assistance with reported bugs and issues
- Help with included theme-related plugins

You have access to a list of all WolfThemes products and their metadata, including the page builder used (Elementor or WPBakery), theme version, last update, demo URL, and category. Use this data to identify the theme and builder involved in any ticket, and tailor your support response accordingly. Always check this metadata before suggesting any feature or troubleshooting step related to Elementor or WPBakery.

You can also use the tool GetThemeBuilder to quickly find out which builder a theme uses based on its slug.

Support does not cover installation or customization services. For these requests, you politely direct customers to our paid services at https://wolfthemes.com/services.

Your goal is efficient resolution of tickets while maintaining customer satisfaction.""",
    tools=[search_kb],
    allow_delegation=False,
    verbose=True
)

if __name__ == "__main__":
    # import cProfile
    # print("✅ Profiling document loading...")
    # cProfile.run('load_all_documents()')
    print("✅ Support agent ready.")
    # Example usage:
    # result = search_kb("stylesheet missing")
    print(f"✅ Script completed in {time.time() - start:.2f} seconds.")

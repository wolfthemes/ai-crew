import json
import html
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from crewai import Agent
from crewai.tools import tool

load_dotenv()

EMBED_PATH = "data/faiss_store"

### -------- Utilities --------

def clean_html_to_text(html_string: str) -> str:
    soup = BeautifulSoup(html.unescape(html_string), "html.parser")
    return soup.get_text(separator="\n", strip=True)

def parse_json_file(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"⚠️ Warning: {path} is empty or missing.")
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            # Handle wrapped structure
            if isinstance(data, dict) and "closed-tickets" in data:
                return data["closed-tickets"]
            return data
    except Exception as e:
        print(f"❌ JSON error in {path}: {str(e)}")
        return []

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

### -------- Loaders --------

def load_kb_articles(path="data/wolfthemes_kb_articles.json"):
    data = parse_json_file(path)
    return format_documents(data, source="kb_article")

def load_theme_docs(path="data/wolfthemes_theme_docs.json"):
    data = parse_json_file(path)
    return format_documents(data, source="theme_doc")

def load_closed_tickets():
    path = "data/wolfthemes_closed_tickets.json"
    data = parse_json_file(path)

    # Unwrap if wrapped
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

### -------- Vector DB --------

def load_or_create_vectorstore(docs):
    embedding = OpenAIEmbeddings()
    if os.path.exists(EMBED_PATH):
        print("🔁 Loading existing FAISS index (trusted)...")
        return FAISS.load_local(EMBED_PATH, embedding, allow_dangerous_deserialization=True)
    else:
        print("✨ Creating new FAISS index...")
        vectorstore = FAISS.from_documents(docs, embedding)
        vectorstore.save_local(EMBED_PATH)
        return vectorstore

### -------- Load All Docs --------

print("📦 Loading knowledge base documents...")

articles = load_kb_articles()
theme_docs = load_theme_docs()
tickets = load_closed_tickets()

all_docs = articles + theme_docs + tickets
print(f"✅ Loaded {len(all_docs)} documents total.")

vectorstore = load_or_create_vectorstore(all_docs)
retriever = vectorstore.as_retriever()

### -------- Tool (CrewAI-Compatible) --------

@tool("SearchKnowledgeBase")
def search_kb(query):
    """Search WolfThemes documentation and support tickets."""
    results = retriever.invoke(query)
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
    backstory="""You are a WordPress support expert for WolfThemes with 
    access to documentation, knowledge base articles, and past resolved tickets. 
    You provide quick, clear, and accurate support to customers.""",
    tools=[search_kb],
    allow_delegation=False,
    verbose=True
)

if __name__ == "__main__":
    print("✅ Support agent ready.")
    # Example usage:
    # result = search_kb("stylesheet missing")
    # print(result)
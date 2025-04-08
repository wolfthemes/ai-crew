import json
import html
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.tools import tool
from crewai import Agent

load_dotenv()

EMBED_PATH = "data/faiss_store"

### -------- Utils --------

def clean_html_to_text(html_string: str) -> str:
    soup = BeautifulSoup(html.unescape(html_string), "html.parser")
    return soup.get_text(separator="\n", strip=True)

def parse_json_file(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"⚠️ Warning: {path} is empty or missing.")
        return []
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
            if all(isinstance(d, str) for d in data):
                return [json.loads(x) for x in data]
            return data
        except Exception as e:
            print(f"❌ Failed to load JSON from {path}: {e}")
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
                **({ "slug": item.get("slug") } if source == "theme_doc" else {})
            }
        ))
    return documents

### -------- Data Loaders --------

def load_kb_articles():
    data = parse_json_file("data/wolfthemes_kb_articles.json")
    return format_documents(data, source="kb_article")

def load_theme_docs():
    data = parse_json_file("data/wolfthemes_theme_docs.json")
    return format_documents(data, source="theme_doc")

def load_closed_tickets():
    data = parse_json_file("data/wolfthemes_closed_tickets.json")
    documents = []
    for t in data:
        if not isinstance(t, dict) or not t.get("ticket_comments"):
            continue
        text_blocks = []
        for c in t["ticket_comments"]:
            if c.get("private") == "1":
                continue
            comment = clean_html_to_text(c.get("comment", ""))
            if comment:
                text_blocks.append(f"{c.get('commenter_name', 'User')}:\n{comment}")
        conversation = "\n\n---\n\n".join(text_blocks)
        if conversation.strip():
            documents.append(Document(
                page_content=conversation.strip(),
                metadata={
                    "title": t.get("ticket_title", "Untitled Ticket"),
                    "url": t.get("related_url", ""),
                    "ticket_id": t.get("ticket_id"),
                    "theme": t.get("envato_verified_string", {}).get("item_name", "Unknown Theme")
                        if isinstance(t.get("envato_verified_string"), dict) else "Unknown Theme",
                    "source": "support_ticket"
                }
            ))
    return documents

### -------- Vector Store --------

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

### -------- Main Process --------

print("📦 Loading knowledge base documents...")

articles = load_kb_articles()
theme_docs = load_theme_docs()
tickets = load_closed_tickets()

all_docs = articles + theme_docs + tickets
print(f"✅ Loaded {len(all_docs)} documents total.")

vectorstore = load_or_create_vectorstore(all_docs)
retriever = vectorstore.as_retriever()

@tool
def search_kb(query: str) -> str:
    """Searches the WolfThemes knowledge base for support issues."""
    results = retriever.invoke(query)
    return "\n\n".join([
        f"Title: {doc.metadata.get('title', 'No title')}\nURL: {doc.metadata.get('url', 'No URL')}\nContent:\n{doc.page_content}"
        for doc in results
    ]) if results else "No relevant content found."

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

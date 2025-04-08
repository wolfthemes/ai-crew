import json
import html
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from crewai import Agent

# Load .env for OpenAI credentials, etc.
load_dotenv()

### -------- Helpers --------

def clean_html_to_text(html_string: str) -> str:
    soup = BeautifulSoup(html.unescape(html_string), "html.parser")
    return soup.get_text(separator="\n", strip=True)

### -------- Load Articles --------

def load_kb_articles(path="data/wolfthemes_kb_articles.json"):
    with open(path, encoding="utf-8") as f:
        kb_data = json.load(f)

    return [
        Document(
            page_content=clean_html_to_text(a["content"]),
            metadata={
                "title": a.get("title", "Untitled Article"),
                "url": a.get("url"),
                "source": "kb_article"
            }
        )
        for a in kb_data if a.get("content")
    ]

### -------- Load Theme Docs --------

def load_theme_docs(path="data/wolfthemes_theme_docs.json"):
    with open(path, encoding="utf-8") as f:
        doc_data = json.load(f)

    return [
        Document(
            page_content=d["content"],
            metadata={
                "title": d.get("title", "Untitled Theme Doc"),
                "url": d.get("url"),
                "slug": d.get("slug"),
                "source": "theme_doc"
            }
        )
        for d in doc_data if d.get("content")
    ]

### -------- Load Closed Tickets --------

def load_closed_tickets(path="data/wolfthemes_closed_tickets.json"):
    with open(path, encoding="utf-8") as f:
        ticket_data = json.load(f)

    documents = []
    for t in ticket_data:
        if not t.get("ticket_comments"):
            continue

        text_blocks = []
        for c in t["ticket_comments"]:
            if c.get("private") == "1":
                continue
            comment = clean_html_to_text(c["comment"])
            text_blocks.append(f"{c['commenter_name']}:\n{comment}")

        conversation = "\n\n---\n\n".join(text_blocks)
        documents.append(Document(
            page_content=conversation.strip(),
            metadata={
                "title": t.get("ticket_title", "Untitled Ticket"),
                "url": t.get("related_url", ""),
                "ticket_id": t.get("ticket_id"),
                "theme": t.get("envato_verified_string", {}).get("item_name", "Unknown Theme") if isinstance(t.get("envato_verified_string"), dict) else "Unknown Theme",
                "source": "support_ticket"
            }
        ))
    return documents

### -------- Create KB Tool --------

class KBSearchTool:
    name = "KB Search Tool"
    description = "Searches the WolfThemes Knowledge Base for answers to theme issues"

    def __init__(self, retriever):
        self.retriever = retriever

    def __call__(self, query: str) -> str:
        results = self.retriever.invoke(query)
        return "\n\n".join([
            f"Title: {doc.metadata.get('title', 'No title')}\nURL: {doc.metadata.get('url', 'No URL')}\nContent:\n{doc.page_content}"
            for doc in results
        ]) if results else "No relevant content found."

### -------- Main Agent Setup --------

print("📦 Loading all knowledge base sources...")

articles = load_kb_articles()
theme_docs = load_theme_docs()
tickets = load_closed_tickets()

all_docs = articles + theme_docs + tickets
print(f"✅ Loaded {len(all_docs)} documents.")

print("🔍 Creating vector store...")
embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(all_docs, embedding)
retriever = vectorstore.as_retriever()

print("🔧 Initializing KB Tool...")
kb_tool = KBSearchTool(retriever)

print("🧠 Creating Support Agent...")
support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory="""You are a WordPress support expert for WolfThemes with 
    access to detailed documentation and resolved support tickets. You use the 
    knowledge base to find accurate, helpful solutions for customers.""",
    tools=[kb_tool],
    allow_delegation=False,
    verbose=True
)

# Optional debug if running standalone
if __name__ == "__main__":
    print("✅ Support agent loaded and ready.")

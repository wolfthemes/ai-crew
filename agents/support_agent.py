
import os
import json
import time
import shutil
import multiprocessing

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from crewai import Agent
from crewai.tools import tool

from utils.helpers import compute_all_file_hashes, hashes_changed
from utils.document_loaders import (
    load_common_issues,
    load_theme_notes,
    load_ticket_examples,
    load_theme_meta,
    load_kb_articles,
    load_theme_docs,
    load_closed_tickets,
    load_backstory
)

start = time.time()
load_dotenv()

# Configuration
DATA_FOLDER = "data"
EMBED_PATH = os.path.join(DATA_FOLDER, "faiss_store")
HASH_PATH = os.path.join(EMBED_PATH, "doc_hash.json")
USE_VECTORSTORE = True
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 1)

### Load all documents
print("📦 Loading knowledge base documents...")

theme_notes = load_theme_notes()
ticket_examples = load_ticket_examples()
theme_meta_docs = load_theme_meta()
articles = load_kb_articles()
theme_docs = load_theme_docs()
tickets = load_closed_tickets()
common_issues = load_common_issues()
backstory_text = load_backstory()

all_docs = theme_meta_docs + theme_notes + ticket_examples + common_issues + articles + theme_docs + tickets
print(f"✅ Loaded {len(all_docs)} documents total.")

### Vectorstore setup
if USE_VECTORSTORE:
    embedding = OpenAIEmbeddings()
    current_hashes = compute_all_file_hashes(DATA_FOLDER)

    if os.path.exists(EMBED_PATH) and os.path.exists(HASH_PATH):
        with open(HASH_PATH, "r") as f:
            stored_hashes = json.load(f)
        if not hashes_changed(stored_hashes, current_hashes):
            print("📦 Loading existing FAISS index (documents unchanged)...")
            vectorstore = FAISS.load_local(EMBED_PATH, embedding)
        else:
            print("🗑️ Document files changed. Rebuilding FAISS index...")
            shutil.rmtree(EMBED_PATH)
            vectorstore = FAISS.from_documents(all_docs, embedding)
            vectorstore.save_local(EMBED_PATH)
            with open(HASH_PATH, "w") as f:
                json.dump(current_hashes, f)
    else:
        print("⚠️ No existing FAISS index or hashes found. Creating new index...")
        if os.path.exists(EMBED_PATH):
            shutil.rmtree(EMBED_PATH)
        vectorstore = FAISS.from_documents(all_docs, embedding)
        vectorstore.save_local(EMBED_PATH)
        with open(HASH_PATH, "w") as f:
            json.dump(current_hashes, f)
    retriever = vectorstore.as_retriever()
else:
    retriever = None
    print("🚫 Vectorstore skipped. Retrieval disabled.")

### Tools

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
    
# Set prioritis to resources type
def rerank_results(results):
    priority_map = {
        "ticket_example": 1,
        "common_issue": 2,
        "kb_article": 3,
        "theme_note": 4,
        "theme_doc": 5,
        "support_ticket": 6
    }
    return sorted(results, key=lambda doc: priority_map.get(doc.metadata.get("source", ""), 99))

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

    results = rerank_results(retriever.invoke(query))

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

### Agent

support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory = backstory_text,
    tools=[search_kb, get_theme_builder],
    allow_delegation=False,
    verbose=True
)

if __name__ == "__main__":
    print(f"✅ Agent initialized in {time.time() - start:.2f} seconds.")

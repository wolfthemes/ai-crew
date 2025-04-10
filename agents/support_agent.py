
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

from tools.kb_tools import rerank_results
from utils.helpers import compute_all_file_hashes, hashes_changed
from utils.document_loaders import (
    load_common_issues,
    load_theme_notes,
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
theme_meta_docs = load_theme_meta()
articles = load_kb_articles()
theme_docs = load_theme_docs()
tickets = load_closed_tickets()
common_issues = load_common_issues()
backstory_text = load_backstory()

all_docs = theme_meta_docs + theme_notes + common_issues + articles + theme_docs + tickets

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

def search_kb_raw(query: str):
    """Raw search function that returns structured string data from the KB"""
    if not retriever:
        return {
            "source": "error",
            "title": "Retrieval Error",
            "content": "Retrieval is disabled. Vectorstore not loaded."
        }

    results = rerank_results(retriever.invoke(query))

    if not results:
        return {
            "source": "none",
            "title": "No Results",
            "content": "No relevant results found in the knowledge base."
        }

    # Return structured data for common issues with a special prefix
    common_issues = [doc for doc in results if doc.metadata.get("issue_type") == "common_issue"]
    if common_issues:
        return {
            "source": "common_issue",
            "title": common_issues[0].metadata.get("title", "Common Issue"),
            "content": f"STRICT_RESPONSE: {common_issues[0].metadata.get('expected_response')}",
            "is_strict": True
        }

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
    

@tool("SearchKnowledgeBase")
def search_kb(query: str):
    """
    Search the common issues, WolfThemes documentation, KB articles, and past tickets for the given query string.
    If a common issue is found, return ONLY the expected_response field as a STRICT_RESPONSE that must be used verbatim.
    """

    if not retriever:
        return "Retrieval is disabled. Vectorstore not loaded."

    results = rerank_results(retriever.invoke(query))

    if not results:
        return "No relevant results found in the knowledge base."

    # Return ONLY expected_response for common issues with a special prefix
    common_issues = [doc for doc in results if doc.metadata.get("issue_type") == "common_issue"]
    if common_issues:
        return f"STRICT_RESPONSE: {common_issues[0].metadata.get('expected_response')}"

    # Fallback: return first few general results
    return "\n\n".join([
        f"📄 {doc.metadata.get('title')} ({doc.metadata.get('source', '')})"
        f"\n🔗 {doc.metadata.get('url', '')}"
        f"\n{doc.page_content[:300]}..."
        for doc in results[:3]
    ]) or "No relevant results found."

### Agent
support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory = backstory_text,
    tools=[search_kb, get_theme_builder],
    allow_delegation=False,
    verbose=True,
    instructions="""
Your job is to answer a customer support ticket.

You MUST follow these steps precisely:
1. Call the `SearchKnowledgeBase` tool using the ticket text.
2. Check if the response begins with "STRICT_RESPONSE:". If it does:
   - Extract the text after "STRICT_RESPONSE:" and use it VERBATIM in your reply
   - Do not modify, elaborate, or add to this response in any way
3. If the response does not begin with "STRICT_RESPONSE:", you may formulate a helpful response based on the retrieved information.
4. Always add a greeting at the beginning and a professional closing at the end.

Format your reply as:
Hi there,

{RESPONSE CONTENT}

I hope this helps!

Best regards,
Support Team
"""
)

if __name__ == "__main__":
    print(f"✅ Agent initialized in {time.time() - start:.2f} seconds.")

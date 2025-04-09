
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
    load_closed_tickets
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
def get_theme_builder(slug: str) -> str:
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
def search_kb(query: str) -> str:
    if not retriever:
        return "Retrieval is disabled. Vectorstore not loaded."

    results = retriever.invoke(query)

    if not results:
        return "No relevant results found in the knowledge base."

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
    tools=[search_kb, get_theme_builder],
    allow_delegation=False,
    verbose=True
)

if __name__ == "__main__":
    print(f"✅ Agent initialized in {time.time() - start:.2f} seconds.")

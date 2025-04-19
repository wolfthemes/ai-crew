import os
import json
import shutil
import multiprocessing

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

from utils.document_loaders import (
    load_common_issues,
    load_reference_tickets,
    load_theme_meta,
    load_kb_articles,
    load_theme_docs,
    load_closed_tickets_from_db,
    load_support_agent_backstory,
    load_support_agent_instructions,
    load_reformulate_agent_instructions,
    load_dev_agent_backstory
)
from utils.helpers import compute_all_file_hashes, hashes_changed

load_dotenv()

# Config
DATA_FOLDER = "data"
EMBED_PATH = os.path.join(DATA_FOLDER, "faiss_store")
HASH_PATH = os.path.join(EMBED_PATH, "doc_hash.json")
USE_VECTORSTORE = True
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 1)

# Load all documents
theme_meta_docs = load_theme_meta()
articles = load_kb_articles()
theme_docs = load_theme_docs()
closed_tickets_from_db = load_closed_tickets_from_db("data/db/closed_tickets.db")
common_issues = load_common_issues()
reference_tickets = load_reference_tickets()
support_agent_backstory_text = load_support_agent_backstory()
support_agent_instructions_text = load_support_agent_instructions()
reformulate_agent_instructions_text = load_reformulate_agent_instructions()

dev_agent_backstory_text = load_dev_agent_backstory()


all_docs = common_issues + reference_tickets + articles + theme_docs + closed_tickets_from_db

# Build or load retriever
if USE_VECTORSTORE:
    embedding = OpenAIEmbeddings()
    current_hashes = compute_all_file_hashes(DATA_FOLDER)

    if os.path.exists(EMBED_PATH) and os.path.exists(HASH_PATH):
        with open(HASH_PATH, "r") as f:
            stored_hashes = json.load(f)
        if not hashes_changed(stored_hashes, current_hashes):
            print("📦 Loading existing FAISS index...")
            vectorstore = FAISS.load_local(EMBED_PATH, embedding)
        else:
            print("🗑️ Rebuilding FAISS index (file hashes changed)...")
            shutil.rmtree(EMBED_PATH)
            vectorstore = FAISS.from_documents(all_docs, embedding)
            vectorstore.save_local(EMBED_PATH)
            with open(HASH_PATH, "w") as f:
                json.dump(current_hashes, f)
    else:
        print("⚠️ No FAISS index found. Creating new index...")
        if os.path.exists(EMBED_PATH):
            shutil.rmtree(EMBED_PATH)
        vectorstore = FAISS.from_documents(all_docs, embedding)
        vectorstore.save_local(EMBED_PATH)
        with open(HASH_PATH, "w") as f:
            json.dump(current_hashes, f)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
else:
    retriever = None

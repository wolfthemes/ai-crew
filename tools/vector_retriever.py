import os
import json
import shutil
import multiprocessing
import logging
import time
from datetime import datetime

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Config
DATA_FOLDER = "data"
EMBED_PATH = os.path.join(DATA_FOLDER, "faiss_store")
HASH_PATH = os.path.join(EMBED_PATH, "doc_hash.json")
TIMESTAMP_PATH = os.path.join(EMBED_PATH, "last_build.txt")
USE_VECTORSTORE = True
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 1)
FORCE_REBUILD = os.environ.get("FORCE_REBUILD_INDEX", "").lower() in ["true", "1", "yes"]
# Maximum age of index in hours before forcing rebuild
MAX_INDEX_AGE_HOURS = float(os.environ.get("MAX_INDEX_AGE_HOURS", "24"))

# Function to check if index is too old
def is_index_too_old():
    if not os.path.exists(TIMESTAMP_PATH):
        logger.info("No timestamp file found, index considered old")
        return True
    
    try:
        with open(TIMESTAMP_PATH, "r") as f:
            timestamp_str = f.read().strip()
        
        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        age_hours = (now - timestamp).total_seconds() / 3600
        
        if age_hours > MAX_INDEX_AGE_HOURS:
            logger.info(f"Index is {age_hours:.1f} hours old (max: {MAX_INDEX_AGE_HOURS}), needs rebuild")
            return True
        else:
            logger.info(f"Index age: {age_hours:.1f} hours (max: {MAX_INDEX_AGE_HOURS}), still fresh")
            return False
    except Exception as e:
        logger.error(f"Error checking index age: {e}")
        return True

# Update timestamp file
def update_timestamp():
    os.makedirs(os.path.dirname(TIMESTAMP_PATH), exist_ok=True)
    with open(TIMESTAMP_PATH, "w") as f:
        f.write(datetime.now().isoformat())

# Load all documents
def load_documents():
    logger.info("Loading documents for vectorization...")
    
    start_time = time.time()
    
    # Load all document types with error handling
    try:
        theme_meta_docs = load_theme_meta()
        logger.info(f"✓ Loaded {len(theme_meta_docs)} theme meta documents")
    except Exception as e:
        logger.error(f"Error loading theme meta docs: {e}")
        theme_meta_docs = []
    
    try:
        articles = load_kb_articles()
        logger.info(f"✓ Loaded {len(articles)} KB articles")
    except Exception as e:
        logger.error(f"Error loading KB articles: {e}")
        articles = []
    
    try:
        theme_docs = load_theme_docs()
        logger.info(f"✓ Loaded {len(theme_docs)} theme docs")
    except Exception as e:
        logger.error(f"Error loading theme docs: {e}")
        theme_docs = []
    
    try:
        closed_tickets_from_db = load_closed_tickets_from_db("data/db/closed_tickets.db")
        logger.info(f"✓ Loaded {len(closed_tickets_from_db)} closed tickets from DB")
    except Exception as e:
        logger.error(f"Error loading closed tickets: {e}")
        closed_tickets_from_db = []
    
    try:
        common_issues = load_common_issues()
        logger.info(f"✓ Loaded {len(common_issues)} common issues")
    except Exception as e:
        logger.error(f"Error loading common issues: {e}")
        common_issues = []
    
    try:
        reference_tickets = load_reference_tickets()
        logger.info(f"✓ Loaded {len(reference_tickets)} reference tickets")
    except Exception as e:
        logger.error(f"Error loading reference tickets: {e}")
        reference_tickets = []
    
    # Load instruction texts (global variables)
    global support_agent_backstory_text, support_agent_instructions_text
    global reformulate_agent_instructions_text, dev_agent_backstory_text
    
    try:
        support_agent_backstory_text = load_support_agent_backstory()
        support_agent_instructions_text = load_support_agent_instructions()
        reformulate_agent_instructions_text = load_reformulate_agent_instructions()
        dev_agent_backstory_text = load_dev_agent_backstory()
    except Exception as e:
        logger.error(f"Error loading instruction texts: {e}")
    
    # Combine all docs for vectorization
    all_docs = common_issues + reference_tickets + articles + theme_docs + closed_tickets_from_db
    
    duration = time.time() - start_time
    logger.info(f"✓ Document loading completed in {duration:.2f} seconds. Total documents: {len(all_docs)}")
    
    return all_docs

# Determine if rebuild is needed
def should_rebuild_index():
    # Force rebuild if specified
    if FORCE_REBUILD:
        logger.info("Forced rebuild requested via environment variable")
        return True
    
    # Check if index exists
    if not os.path.exists(EMBED_PATH) or not os.path.exists(HASH_PATH):
        logger.info("No existing index or hash file found")
        return True
    
    # Check if index is too old
    if is_index_too_old():
        return True
    
    # Check if content has changed
    try:
        current_hashes = compute_all_file_hashes(DATA_FOLDER)
        with open(HASH_PATH, "r") as f:
            stored_hashes = json.load(f)
        
        if hashes_changed(stored_hashes, current_hashes):
            logger.info("File hashes have changed - rebuilding index")
            return True
    except Exception as e:
        logger.error(f"Error comparing hashes: {e}")
        return True
    
    logger.info("✓ No changes detected - using existing index")
    return False

# Build or load vectorstore
retriever = None

if USE_VECTORSTORE:
    try:
        # Load embedding model
        embedding = OpenAIEmbeddings()
        
        # Check if rebuild is needed
        rebuild_needed = should_rebuild_index()
        
        if rebuild_needed:
            logger.info("🔨 Building new FAISS index...")
            
            # Remove old index if it exists
            if os.path.exists(EMBED_PATH):
                try:
                    shutil.rmtree(EMBED_PATH)
                except Exception as e:
                    logger.error(f"Error removing old index: {e}")
            
            # Create directory if it doesn't exist
            os.makedirs(EMBED_PATH, exist_ok=True)
            
            # Load documents
            all_docs = load_documents()
            
            if all_docs:
                # Compute current file hashes
                current_hashes = compute_all_file_hashes(DATA_FOLDER)
                
                # Build the index
                start_time = time.time()
                vectorstore = FAISS.from_documents(all_docs, embedding)
                build_time = time.time() - start_time
                logger.info(f"✓ FAISS index built in {build_time:.2f} seconds")
                
                # Save the index
                try:
                    vectorstore.save_local(EMBED_PATH)
                    logger.info("✓ FAISS index saved to disk")
                except Exception as e:
                    logger.error(f"Error saving FAISS index: {e}")
                
                # Save hashes and timestamp
                try:
                    with open(HASH_PATH, "w") as f:
                        json.dump(current_hashes, f)
                    logger.info("✓ File hashes saved")
                    
                    update_timestamp()
                    logger.info("✓ Timestamp updated")
                except Exception as e:
                    logger.error(f"Error saving hashes or timestamp: {e}")
                
                # Create retriever
                retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
            else:
                logger.error("No documents to index")
                retriever = None
        else:
            # Load existing index
            logger.info("📦 Loading existing FAISS index...")
            try:
                start_time = time.time()
                vectorstore = FAISS.load_local(EMBED_PATH, embedding)
                load_time = time.time() - start_time
                logger.info(f"✓ FAISS index loaded in {load_time:.2f} seconds")
                
                # Create retriever
                retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                # Fall back to rebuilding
                logger.info("⚠️ Falling back to rebuilding index...")
                
                # Load documents
                all_docs = load_documents()
                
                if all_docs:
                    # Compute current file hashes
                    current_hashes = compute_all_file_hashes(DATA_FOLDER)
                    
                    # Build the index
                    vectorstore = FAISS.from_documents(all_docs, embedding)
                    vectorstore.save_local(EMBED_PATH)
                    
                    # Save hashes and timestamp
                    with open(HASH_PATH, "w") as f:
                        json.dump(current_hashes, f)
                    
                    update_timestamp()
                    
                    # Create retriever
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
                else:
                    logger.error("No documents to index")
                    retriever = None
    except Exception as e:
        logger.error(f"Unhandled error in vectorstore initialization: {e}")
        retriever = None
else:
    logger.info("ℹ️ Vectorstore disabled by configuration")
    retriever = None

# These need to be defined even if not set in the code above
if 'support_agent_backstory_text' not in globals():
    support_agent_backstory_text = "Support Agent Backstory not loaded"
    
if 'support_agent_instructions_text' not in globals():
    support_agent_instructions_text = "Support Agent Instructions not loaded"
    
if 'reformulate_agent_instructions_text' not in globals():
    reformulate_agent_instructions_text = "Reformulate Agent Instructions not loaded"
    
if 'dev_agent_backstory_text' not in globals():
    dev_agent_backstory_text = "Dev Agent Backstory not loaded"
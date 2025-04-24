
import logging
import os
import re
import json
import html
import hashlib
from functools import lru_cache
import html2text
from bs4 import BeautifulSoup
import time
from datetime import datetime

import logging
import os
from datetime import datetime
import sys

def setup_logging(log_dir="logs"):
    """Set up basic logging configuration with UTF-8 safe console output"""
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    log_filename = f"{log_dir}/process_{timestamp}.log"

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")

    # Ensure UTF-8 support for console
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[file_handler, console_handler]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    return logger

# Set up logging for current file
logger = setup_logging()

def compute_file_hash(file_path):
    """
    Compute SHA-256 hash of a file
    """
    try:
        if not os.path.isfile(file_path):
            return None
        
        # Skip files larger than 100MB
        if os.path.getsize(file_path) > 100 * 1024 * 1024:
            return f"large_file_{os.path.getsize(file_path)}"
        
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        # Return modified time as fallback
        try:
            return f"mtime_{os.path.getmtime(file_path)}"
        except:
            return f"error_{time.time()}"

def compute_all_file_hashes(base_path, ignore_dirs=None):
    """
    Compute hashes for all files in directory tree
    
    Args:
        base_path: Root directory to scan
        ignore_dirs: List of directory names to ignore
        
    Returns:
        Dictionary of {file_path: hash_value}
    """
    if ignore_dirs is None:
        ignore_dirs = ['.git', '__pycache__', 'node_modules', 'faiss_store']
    
    hashes = {}
    try:
        start_time = time.time()
        file_count = 0
        
        # Walk directory tree
        for root, dirs, files in os.walk(base_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # Skip temporary files
                if file.startswith('.') or file.endswith('~'):
                    continue
                
                # Skip large binary files and certain extensions
                if file.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe')):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_path)
                
                # Compute file hash
                file_hash = compute_file_hash(file_path)
                if file_hash:
                    hashes[rel_path] = file_hash
                    file_count += 1
        
        duration = time.time() - start_time
        logger.info(f"Computed hashes for {file_count} files in {duration:.2f} seconds")
        return hashes
    
    except Exception as e:
        logger.error(f"Error computing file hashes: {e}")
        return {}

def hashes_changed(old_hashes, new_hashes):
    """
    Compare two hash dictionaries and detect if files have changed
    
    Returns:
        Boolean: True if changes detected, False otherwise
    """
    try:
        # Check for added or modified files
        for file_path, new_hash in new_hashes.items():
            # File is new
            if file_path not in old_hashes:
                logger.info(f"New file detected: {file_path}")
                return True
            
            # File was modified
            if old_hashes[file_path] != new_hash:
                logger.info(f"Modified file detected: {file_path}")
                return True
        
        # Check for deleted files that matter
        for file_path in old_hashes:
            key_files = ['common_issues.json', 'reference_tickets.json']
            if file_path not in new_hashes and any(kf in file_path for kf in key_files):
                logger.info(f"Key file removed: {file_path}")
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error comparing hashes: {e}")
        # Default to changed if comparison fails
        return True

def clean_html_to_text(html_string) -> str:
    if not isinstance(html_string, (str, bytes)):
        html_string = str(html_string)
    soup = BeautifulSoup(html.unescape(html_string), "html.parser")
    return soup.get_text(separator="\n", strip=True)

def convert_html_to_markdown(html_string):
    if not isinstance(html_string, str):
        html_string = str(html_string)
    handler = html2text.HTML2Text()
    handler.ignore_links = False  # Keep links
    handler.ignore_images = True
    handler.body_width = 0  # Prevent line wrapping
    return handler.handle(html_string).strip()

def convert_html_to_plaintext_with_urls(html_string):
    if not isinstance(html_string, str):
        html_string = str(html_string)

    soup = BeautifulSoup(html.unescape(html_string), "html.parser")

    # Convert <br> to \n
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Convert links: <a href="...">text</a> → text (URL)
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href", "").strip()
        a.replace_with(f"{text} ({href})" if href else text)

    # Extract text content with spacing logic
    lines = []
    for elem in soup.find_all(["p", "div", "li"]):
        text = elem.get_text(" ", strip=True)
        if text:
            lines.append(text)

    # Add paragraphs only once, separated by blank lines
    return "\n\n".join(lines).strip()

@lru_cache(maxsize=20)
def parse_json_file(path):
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
    
# Helper: format "time ago"
def time_ago(timestamp_str):
    try:
        posted_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        seconds = int(time.time() - posted_time.timestamp())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except:
        return "—"
    
# Strip basic HTML tags for sidebar
def strip_html_tags(text):
    return re.sub(r"<.*?>", "", html.unescape(text)).strip()
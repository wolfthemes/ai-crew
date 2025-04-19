
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

@lru_cache(maxsize=100)
def compute_file_hash(filepath):
    """Compute MD5 hash of a file with caching."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compute_all_file_hashes(folder_path):
    file_hashes = {}
    for root, _, files in sorted(os.walk(folder_path)):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath):
                file_hashes[os.path.relpath(fpath, folder_path)] = compute_file_hash(fpath)
    return file_hashes

def hashes_changed(stored_hashes, current_hashes):
    return stored_hashes != current_hashes

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

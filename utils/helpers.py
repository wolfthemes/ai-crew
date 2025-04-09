
import os
import json
import html
import hashlib
from functools import lru_cache
from bs4 import BeautifulSoup

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

def clean_html_to_text(html_string: str) -> str:
    soup = BeautifulSoup(html.unescape(html_string), "html.parser")
    return soup.get_text(separator="\n", strip=True)

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

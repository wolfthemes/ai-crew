import os
import json
import base64
import requests
import re
from dotenv import load_dotenv

load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "wolfthemes/wolf-supertheme"
SLUGS_PATH = "theme-slugs.json"
OUTPUT_PATH = "data/themes/theme_catalog.json"

def get_theme_slugs():
    print("📥 Fetching theme slugs from private GitHub repo via API...")
    api_url = f"https://api.github.com/repos/{REPO}/contents/{SLUGS_PATH}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(api_url, headers=headers, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch theme slugs ({response.status_code})\n{response.text}")
    content_data = response.json()
    decoded_content = base64.b64decode(content_data["content"]).decode("utf-8")
    return json.loads(decoded_content)["theme_slugs"]

def fetch_theme_config(slug):
    # Use GitHub API endpoint instead of raw URL
    api_url = f"https://api.github.com/repos/{REPO}/contents/THEMES/{slug}/app.config.json"
    headers = {
        "Accept": "application/vnd.github.raw",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    print(f"🔗 Fetching {slug} config")
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"⚠️ Error fetching config for {slug}: {e}")
        return None
    
def fetch_theme_meta(slug):
    # Use GitHub API endpoint instead of raw URL
    api_url = f"https://api.github.com/repos/{REPO}/contents/THEMES/{slug}/theme_meta.json"
    headers = {
        "Accept": "application/vnd.github.raw",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    print(f"🔗 Fetching {slug} meta")
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"⚠️ Error fetching meta for {slug}: {e}")
        return None
    
def fetch_theme_description(slug):
    # Use GitHub API endpoint instead of raw URL
    api_url = f"https://api.github.com/repos/{REPO}/contents/THEMES/{slug}/html/description.html"
    headers = {
        "Accept": "application/vnd.github.raw",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    print(f"🔗 Fetching {slug} description")
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"⚠️ Error fetching config for {slug}: {e}")
        return None

def extract_metadata(config):
    return {
        "name": config.get("name"),
        "slug": config.get("slug"),
        "builder": config.get("builder"),
        "url": config.get("url"),
        "demourl": config.get("demourl"),
        "shortlink": config.get("shortlink"),
        "itemId": config.get("itemId"),
        "version": config.get("version"),
        "updated": config.get("updated"),
        "description": config.get("description", ""),
        "category": config.get("category", []),
        "features": config.get("features", []),
        "selling_points": config.get("selling_points", []),
        "theme_style": config.get("theme_style", []),
        "target_audience": config.get("target_audience", []),
        "key_benefits": config.get("key_benefits", []),
        "compatible_plugins": config.get("compatible_plugins", []),
        "design_features": config.get("design_features", []),
        "use_cases": config.get("use_cases", []),
        "customer_sites": config.get("customer_sites", []),
        "testimonials": config.get("testimonials", []),
    }

def main():
    os.makedirs("data/themes", exist_ok=True)
    theme_meta = {}

    slugs = get_theme_slugs()
    print(f"🔍 Found {len(slugs)} slugs.")

    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] Processing: {slug}")
        config = fetch_theme_config(slug)
        meta = fetch_theme_meta(slug)
        description = fetch_theme_description(slug)
        
        if config:

            if meta:
                config = {**config, **meta}

            if description:
                text_only = re.sub(r'<[^>]+>', '', description)
                clean_description = re.sub(r'\s+', ' ', text_only).strip()
                config["description"] = clean_description

            theme_meta[slug] = extract_metadata(config)


    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(theme_meta, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved theme metadata to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

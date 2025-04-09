import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "wolfthemes/wolf-supertheme"
SLUGS_PATH = "theme-slugs.json"
OUTPUT_PATH = "data/theme_info.json"

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
    
    print(f"🔗 Fetching: {api_url}")
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
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
        "version": config.get("version"),
        "updated": config.get("updated"),
        "category": config.get("category"),
    }

def main():
    os.makedirs("data", exist_ok=True)
    theme_meta = {}

    slugs = get_theme_slugs()
    print(f"🔍 Found {len(slugs)} slugs.")

    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] Processing: {slug}")
        config = fetch_theme_config(slug)
        if config:
            theme_meta[slug] = extract_metadata(config)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(theme_meta, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved theme metadata to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

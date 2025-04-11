import os
import json
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from markdownify import markdownify as md

load_dotenv()

# Load theme slugs from GitHub
import base64
import requests

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "wolfthemes/wolf-supertheme"
FILE_PATH = "theme-slugs.json"
DOC_BASE_URL = "https://doc.wolfthemes.com/theme/"

def get_theme_slugs():
    print("📥 Fetching theme slugs from private GitHub repo via API...")
    api_url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(api_url, headers=headers, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch theme slugs ({response.status_code})\n{response.text}")
    content_data = response.json()
    decoded_content = base64.b64decode(content_data["content"]).decode("utf-8")
    return json.loads(decoded_content)["theme_slugs"]

def fetch_doc_content(page, slug):
    url = f"{DOC_BASE_URL}{slug}/"
    try:
        page.goto(url, timeout=15000)
        page.wait_for_selector("#page", timeout=10000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        content_section = soup.select_one("#page") or soup.body

        title = soup.title.string.strip() if soup.title else slug
        return {
            "slug": slug,
            "url": url,
            "title": title,
            "content": md(content_section.decode_contents().strip(), heading_style="ATX")
        }

    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return None

def main():
    slugs = get_theme_slugs()
    print(f"🔗 Found {len(slugs)} theme slugs.")
    docs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, slug in enumerate(slugs, 1):
            print(f"[{i}/{len(slugs)}] Fetching: {slug}")
            doc = fetch_doc_content(page, slug)
            if doc:
                docs.append(doc)
            time.sleep(0.5)  # polite delay

        browser.close()

    os.makedirs("data/crawled", exist_ok=True)
    with open("data/crawled/theme_docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(docs)} docs to data/crawled/theme_docs.json")

if __name__ == "__main__":
    main()

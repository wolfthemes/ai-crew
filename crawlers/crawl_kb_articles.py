import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://wolfthemes.ticksy.com"
ARTICLE_LIST_URL = f"{BASE_URL}/articles/"

def get_article_links():
    print("🔎 Crawling article links...")
    response = requests.get(ARTICLE_LIST_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    # The articles are listed in <a> tags with hrefs containing '/article/'
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/article/" in href:
            full_url = BASE_URL + href if not href.startswith("http") else href
            if full_url not in links:
                links.append(full_url)

    return list(set(links))

def fetch_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        article_section = soup.select_one("#single-article")
        if not article_section:
            print(f"⚠️ Article content not found at {url}")
            return None

        title = article_section.select_one("h1.page-title")
        content = article_section.select_one(".article-content")
        if not title or not content:
            print(f"⚠️ Missing title or content in article {url}")
            return None

        return {
            "title": title.get_text(strip=True),
            "url": url,
            "content": content.decode_contents().strip()
        }
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        with open("errors.log", "a", encoding="utf-8") as log:
            log.write(f"{url} - {e}\n")
        return None

def main():
    links = get_article_links()
    print(f"🔗 Found {len(links)} articles.")
    articles = []

    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Fetching: {link}")
        article = fetch_article_content(link)
        if article:
            articles.append(article)
        time.sleep(1)  # be nice to the server

    with open("data/crawled/wolfthemes_kb_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(articles)} articles to data/crawled/kb_articles.json")

if __name__ == "__main__":
    main()

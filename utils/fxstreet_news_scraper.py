# utils/fxstreet_news_scraper.py
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime, timedelta
import re

# Reuse the same USER_AGENTS from your downloader
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def get_fxstreet_news(currency_pair="EURUSD", max_articles=10, force_refresh=False):
    """
    Scrape news articles from FXStreet for a specific currency pair
    
    Args:
        currency_pair (str): Currency pair, e.g., "EURUSD", "GBPUSD", etc.
        max_articles (int): Maximum number of articles to retrieve
        force_refresh (bool): Force refresh even if cached
        
    Returns:
        list: List of news article dictionaries
    """
    # Create a cache file name based on currency pair
    currency_pair = currency_pair.replace("/", "")  # Remove slash if present (EUR/USD -> EURUSD)
    cache_file = f"data/crawled/fxstreet_news_{currency_pair.lower()}.json"
    cache_dir = os.path.dirname(cache_file)
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check if we have cached news that's recent (less than 2 hours old)
    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
            
        # Check cache age (2 hours)
        if "timestamp" in cached_data:
            cache_time = datetime.fromtimestamp(cached_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 7200:  # 2 hours
                print(f"✅ Using cached news for {currency_pair} (less than 2 hours old)")
                return cached_data["articles"]
    
    # Build the URL for the request
    url = f"https://www.fxstreet.com/news?q=&hPP=17&idx=FxsIndexPro&p=0&dFR%5BTags%5D%5B0%5D={currency_pair}"
    
    # Set up headers to mimic a browser
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "user-agent": random.choice(USER_AGENTS),
        "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "referer": "https://www.fxstreet.com/"
    }
    
    try:
        # Fetch the page
        print(f"🔄 Fetching news for {currency_pair}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all article elements
        article_elements = soup.select("div.fxs_listItem")
        articles = []
        
        for article in article_elements[:max_articles]:
            try:
                # Extract title
                title_element = article.select_one("h4.fxs_headline_tiny a")
                title = title_element.get_text(strip=True) if title_element else "N/A"
                
                # Extract URL
                url = title_element["href"] if title_element and "href" in title_element.attrs else "N/A"
                if url.startswith("/"):
                    url = "https://www.fxstreet.com" + url
                
                # Extract summary
                summary_element = article.select_one("p.fxs_entradilla")
                summary = summary_element.get_text(strip=True) if summary_element else "N/A"
                
                # Extract date
                date_element = article.select_one("time.fxs_entry_metaInfo_datePublished")
                date_text = date_element.get("datetime", "") if date_element else ""
                
                # Parse date string
                try:
                    if date_text:
                        # Handle ISO format
                        if "T" in date_text:
                            article_date = datetime.fromisoformat(date_text.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                        else:
                            # Try other formats
                            article_date = datetime.strptime(date_text, "%Y-%m-%d").strftime("%Y-%m-%d")
                    else:
                        # Look for other date formats
                        date_text = date_element.get_text(strip=True) if date_element else ""
                        if "ago" in date_text.lower():
                            # Handle relative dates like "5 hours ago"
                            article_date = datetime.now().strftime("%Y-%m-%d")
                        else:
                            article_date = "N/A"
                except Exception:
                    article_date = "N/A"
                
                # Extract author
                author_element = article.select_one("span.fxs_author_name")
                author = author_element.get_text(strip=True) if author_element else "FXStreet"
                
                articles.append({
                    "date": article_date,
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "author": author,
                    "source": "FXStreet",
                    "currency_pair": currency_pair
                })
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
        
        # Save to cache
        cache_data = {
            "timestamp": datetime.now().timestamp(),
            "currency_pair": currency_pair,
            "articles": articles
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
            
        print(f"✅ Saved {len(articles)} news articles for {currency_pair}")
        return articles
    
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        
        # Try to use cached data even if it's old
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                print(f"⚠️ Using older cached news as fallback for {currency_pair}")
                return cached_data["articles"]
            except Exception:
                pass
                
        return []

def get_fx_news_for_pair(currency_pair):
    """
    Simple wrapper to get formatted news for a currency pair
    
    Args:
        currency_pair (str): Either formatted as "EUR/USD" or "EURUSD"
    
    Returns:
        list: News articles
    """
    # Normalize currency pair format
    normalized_pair = currency_pair.replace("/", "")
    return get_fxstreet_news(currency_pair=normalized_pair)

def get_daily_news():
    """
    Get today's news for major currency pairs
    
    Returns:
        dict: News articles by currency pair
    """
    major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    news_by_pair = {}
    
    for pair in major_pairs:
        news_by_pair[pair] = get_fxstreet_news(pair, max_articles=5)
        # Be nice to the server
        time.sleep(1)
    
    return news_by_pair
import feedparser
import json
import os
import re
import time
from datetime import datetime

def get_eurusd_news(max_cache_age_minutes=60):
    """
    Fetches EUR/USD news from RSS feeds, caches them to JSON, and returns the data.
    
    Args:
        cache_file: Path to the JSON cache file
        max_cache_age_minutes: Maximum age of cache in minutes before refreshing
    
    Returns:
        List of EUR/USD news items
    """
    # Check if cache exists and is recent enough
    cache_file="data/crawled/fxstreet_eurusd_news_cache.json"
    if os.path.exists(cache_file):
        # Get the file modification time
        file_mod_time = os.path.getmtime(cache_file)
        current_time = time.time()
        # Calculate how old the cache is in minutes
        cache_age_minutes = (current_time - file_mod_time) / 60
        
        # If cache is fresh enough, load and return it
        if cache_age_minutes < max_cache_age_minutes:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    print(f"Using cached data from {cache_file}")
                    print(f"Using cached data ({cache_age_minutes:.1f} minutes old)")
                    return cached_data
            except (json.JSONDecodeError, UnicodeDecodeError):
                print("Cache file is corrupted, fetching fresh data")
    
    # If we get here, we need to fetch fresh data
    print("Fetching fresh EUR/USD news data...")
    
    # Parse the news RSS feed
    news_feed = feedparser.parse('https://www.fxstreet.com/rss/news')
    
    # Parse the analysis RSS feed
    analysis_feed = feedparser.parse('https://www.fxstreet.com/rss/analysis')
    
    # Combine both feeds
    all_entries = news_feed.entries + analysis_feed.entries
    
    # Filter for EUR/USD related entries
    eurusd_entries = []
    for entry in all_entries:
        # Check if EUR/USD appears in the title or description
        title = entry.title if hasattr(entry, 'title') else ""
        description = entry.description if hasattr(entry, 'description') else ""
        content = entry.content[0].value if hasattr(entry, 'content') and entry.content else ""
        
        # Check for EUR/USD mentions (case insensitive)
        if re.search(r'EUR/USD|EURUSD', title + description + content, re.IGNORECASE):
            eurusd_entries.append({
                'title': title,
                'description': description,
                'link': entry.link,
                'published': entry.published if hasattr(entry, 'published') else "",
                'published_parsed': time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else None,
                'author': entry.author if hasattr(entry, 'author') else "FXStreet"
            })
    
    # Sort by publication date (newest first)
    eurusd_entries.sort(key=lambda x: x.get('published_parsed', 0), reverse=True)
    
    # Add timestamp of when we fetched this data
    cached_data = {
        'last_updated': datetime.now().isoformat(),
        'entries': eurusd_entries
    }
    
    # Save to cache file
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cached_data, f, indent=2, ensure_ascii=False)
        print(f"Cached {len(eurusd_entries)} EUR/USD news items to {cache_file}")
    except Exception as e:
        print(f"Error caching data: {e}")
    
    return cached_data
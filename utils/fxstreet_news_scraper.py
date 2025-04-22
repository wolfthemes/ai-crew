import feedparser
import re

def get_eurusd_news():
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
                'author': entry.author if hasattr(entry, 'author') else "FXStreet"
            })
    
    return eurusd_entries

# Use the function
#eurusd_news = get_eurusd_news()

# Print the results
# for i, news in enumerate(eurusd_news, 1):
#     print(f"{i}. {news['title']}")
#     print(f"   Published: {news['published']}")
#     print(f"   Author: {news['author']}")
#     print(f"   Link: {news['link']}")
#     print(f"   {news['description'][:150]}...")
#     print()
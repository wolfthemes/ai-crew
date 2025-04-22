import sys
import json
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_news_scraper import get_eurusd_news

news = get_eurusd_news()
print(json.dumps(news, indent=2))
import sys
import json
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_news_scraper import get_fxstreet_news

news = get_fxstreet_news("EURUSD", max_articles=5)
print(json.dumps(news, indent=2))
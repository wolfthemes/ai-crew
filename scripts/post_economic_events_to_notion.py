# scripts/post_economic_events_to_notion.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from datetime import datetime, timedelta, UTC

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_events_downloader import get_fxstreet_events

def main():
    """Post economic events to Notion"""
    load_dotenv()
    
    # Verify environment variables
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_db_key = os.getenv("NOTION_ECONOMIC_EVENTS_DB_KEY")
    
    if not notion_api_key or not notion_db_key:
        print("❌ Notion environment variables not set")
        return False
    
    events = get_fxstreet_events()

    today = datetime.today().strftime("%Y-%m-%d")
    todays_events = [e for e in events if e["date"] == today]

    if todays_events:
        warning_text = "⚠️ Economic News Today:\n" + "\n".join(
            f"- {e['time']} | {e['currency']} | {e['event']} ({e['impact']} impact)" for e in todays_events
        )
    else:
        warning_text = "✅ No major economic events today."

    print( warning_text )

if __name__ == "__main__":
    main()


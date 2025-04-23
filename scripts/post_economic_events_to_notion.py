#!/usr/bin/env python3
# scripts/post_economic_events_to_notion.py
import os
import sys
from pathlib import Path
from notion_client import Client
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_events_downloader import get_fxstreet_events

def post_single_event_to_notion(event, notion_client, database_id, emoji="🚨"):
    """Post a single economic event to Notion as its own page"""
    # Create the page
    response = notion_client.pages.create(
        parent={"database_id": database_id},
        icon={
            "type": "emoji",
            "emoji": emoji
        },
        properties={
            "Name": {"title": [{"text": {"content": event["event"]}}]},
            "Date": {"date": {"start": event["date"]}},
            "Time": {"rich_text": [{"text": {"content": event["time"]}}]},
            "Currency": {"rich_text": [{"text": {"content": event["currency"]}}]},
        }
    )
    
    print(f"✅ Created Notion page for event: {event['event']}")
    return response

def main():
    """Post economic events to Notion"""
    load_dotenv()
    
    # Verify environment variables
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_db_key = os.getenv("NOTION_ECONOMIC_EVENTS_DB_KEY")
    
    if not notion_api_key or not notion_db_key:
        print("❌ Notion environment variables not set")
        return False
    
    # Get all events from the API
    all_events = get_fxstreet_events()
    print(f"📅 Retrieved {len(all_events)} events from FXStreet")
    
    # Setup Notion client
    notion = Client(auth=notion_api_key)
    
    # Sort events by date and time
    all_events.sort(key=lambda x: (x["date"], x["time"]))
    
    # Post each event individually
    if all_events:
        for event in all_events:
            post_single_event_to_notion(event, notion, notion_db_key)
        print(f"✅ Posted {len(all_events)} events to Notion")
    else:
        print("❌ No events found")

if __name__ == "__main__":
    main()
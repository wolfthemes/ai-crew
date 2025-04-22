#!/usr/bin/env python3
# scripts/post_economic_events_to_notion.py
import os
import sys
from pathlib import Path
from notion_client import Client
from dotenv import load_dotenv
import argparse
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_events_downloader import get_fxstreet_events

def post_events_to_notion(events, notion_client, database_id, title_prefix="Economic Events", emoji="📊"):
    """Post a list of events to Notion database"""
    if not events:
        print(f"✅ No events to post")
        return
    
    # Get the date of the first event for the page title
    base_date = events[0]["date"]
    
    # Create summary text for the page - each event on a new line
    summary_lines = []
    
    # Add each event with plain formatting
    for e in events:
        summary_lines.append(f"{e['event']} | {e['time']} | {e['currency']}")
    
    summary_text = "\n".join(summary_lines)
    
    # Create the page
    response = notion_client.pages.create(
        parent={"database_id": database_id},
        icon={
            "type": "emoji",
            "emoji": emoji
        },
        properties={
            "Name": {"title": [{"text": {"content": summary_text}}]},
            "Date": {"date": {"start": base_date}},
        }
    )
    
    print(f"✅ Created Notion page for {base_date} with {len(events)} events")
    return response

def get_date_range(days=1, start_date=None):
    """Get a date range starting from today or a specified date"""
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = datetime.today()
    
    end = start + timedelta(days=days-1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def main():
    """Post economic events to Notion"""
    parser = argparse.ArgumentParser(description="Post economic events to Notion")
    parser.add_argument("--today", action="store_true", help="Post only today's events")
    parser.add_argument("--week", action="store_true", help="Post the whole week's events in a single page")
    parser.add_argument("--days", type=int, default=7, help="Number of days to include (default: 7)")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--daily", action="store_true", help="Post each day's events as separate pages")
    args = parser.parse_args()
    
    load_dotenv()
    
    # Verify environment variables
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_db_key = os.getenv("NOTION_ECONOMIC_EVENTS_DB_KEY")
    
    if not notion_api_key or not notion_db_key:
        print("❌ Notion environment variables not set")
        return False
    
    # Get all events from the API
    all_events = get_fxstreet_events()
    
    # Setup Notion client
    notion = Client(auth=notion_api_key)
    
    # Handle different posting modes
    if args.today:
        # Post only today's events
        today = datetime.today().strftime("%Y-%m-%d")
        todays_events = [e for e in all_events if e["date"] == today]
        
        if todays_events:
            post_events_to_notion(
                todays_events, 
                notion, 
                notion_db_key, 
                title_prefix="⚠️ Economic News Today",
                emoji="🚨"
            )
        else:
            print("✅ No major economic events today.")
    
    elif args.week:
        # Post whole week's events as a single page
        start_date, end_date = get_date_range(args.days, args.start_date)
        
        # Filter events for the date range
        week_events = [e for e in all_events if start_date <= e["date"] <= end_date]
        
        # Sort events by date and time
        week_events.sort(key=lambda x: (x["date"], x["time"]))
        
        # Post to Notion
        post_events_to_notion(
            week_events, 
            notion, 
            notion_db_key, 
            title_prefix=f"📅 Weekly Economic Events ({start_date} to {end_date})",
            emoji="🚨"
        )
    
    elif args.daily:
        # Post each day's events as separate pages
        start_date, end_date = get_date_range(args.days, args.start_date)
        
        # Get all dates in the range
        dates = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current <= end:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        # Post each day's events
        for date in dates:
            day_events = [e for e in all_events if e["date"] == date]
            
            if day_events:
                post_events_to_notion(
                    day_events, 
                    notion, 
                    notion_db_key, 
                    title_prefix="📅 Daily Economic Events",
                    emoji="🚨"
                )
            else:
                print(f"✅ No events for {date}")
    
    else:
        # Default: Post today's events
        today = datetime.today().strftime("%Y-%m-%d")
        todays_events = [e for e in all_events if e["date"] == today]
        
        if todays_events:
            post_events_to_notion(
                todays_events, 
                notion, 
                notion_db_key, 
                title_prefix="⚠️ Economic News Today",
                emoji="🚨"
            )
        else:
            print("✅ No major economic events today.")

if __name__ == "__main__":
    main()
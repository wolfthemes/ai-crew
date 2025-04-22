# utils/fxstreet_downloader.py
import json
import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def get_fxstreet_events(period="week", force_refresh=False):
    """
    Get FXStreet economic events with caching support
    
    Args:
        period (str): Either 'week', 'next_week', 'day', or a specific date string in 'YYYY-MM-DD' format
        force_refresh (bool): If True, forces a download even if cached data exists
    
    Returns:
        list: A list of economic event dictionaries
    """
    # Determine date range based on period
    if period == "week":
        start, end = get_current_week_range()
        week_id = start.strftime("%Y-%m-%d")  # e.g. "2025-04-22"
    elif period == "next_week":
        start, end = get_next_week_range()
        week_id = start.strftime("%Y-%m-%d")  # e.g. "2025-04-29"
    elif period == "day":
        # For day queries, we still use the weekly data but filter afterward
        start, end = get_current_week_range()
        week_id = start.strftime("%Y-%m-%d")
    else:
        # Default to current week for any other input
        start, end = get_current_week_range()
        week_id = start.strftime("%Y-%m-%d")
    
    # Check if cached data exists
    if not force_refresh and json_exists(week_id):
        # Load cached data
        print(f"✅ Using existing data for {period} (week of {week_id})")
        events = load_json_events(week_id)
        
        # Filter for day if needed
        if period == "day":
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return filter_events_by_date(events, today_str)
        elif isinstance(period, str) and len(period) == 10:  # YYYY-MM-DD format
            return filter_events_by_date(events, period)
        else:
            return events
    
    # If we need to download new data (only happens if JSON doesn't exist or force_refresh=True)
    if force_refresh or not json_exists(week_id):
        print(f"🔄 Need to download data for week of {week_id}")
        download_fxstreet_csv_authenticated(week_id)
    
    # Load the JSON data (which should now exist)
    if json_exists(week_id):
        events = load_json_events(week_id)
        
        # Apply filters if needed
        if period == "day":
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return filter_events_by_date(events, today_str)
        elif isinstance(period, str) and len(period) == 10:  # YYYY-MM-DD format
            return filter_events_by_date(events, period)
        
        return events
    else:
        print(f"❌ Failed to get data for week of {week_id}")
        return []

def download_fxstreet_csv_authenticated(week_id=None):
    """
    Download FXStreet CSV data for a specific week and convert to JSON
    
    Args:
        week_id (str): Week identifier in YYYY-MM-DD format (defaults to current week)
    
    Returns:
        str: Path to the saved JSON file
    """
    if week_id is None:
        start, end = get_current_week_range()
        week_id = start.strftime("%Y-%m-%d")  # e.g. "2025-04-22"
    else:
        # If week_id is provided, parse it to get start/end dates
        try:
            start_date = datetime.strptime(week_id, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            start = start_date
            end = start + timedelta(days=6)
        except ValueError:
            # Default to current week if format is invalid
            start, end = get_current_week_range()
            week_id = start.strftime("%Y-%m-%d")
    
    from_date, to_date = format_date_range(start, end)
    url = build_fxstreet_url(from_date, to_date)
    
    if json_exists(week_id):
        print(f"✅ Data for week starting {week_id} already exists. Skipping download.")
        return f"data/crawled/fxstreet_{week_id}.json"
    
    headers = {
        "accept": "text/csv",
        "accept-language": "en-US,en;q=0.7",
        "origin": "https://www.fxstreet.com",
        "priority": "u=1, i",
        "referer": "https://www.fxstreet.com/",
        "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "sec-gpc": "1",
        "user-agent": random.choice(USER_AGENTS)
    }

    os.makedirs("data/crawled", exist_ok=True)
    filename = f"data/crawled/fxstreet_{week_id}.json"

    try:
        print(f"🔄 Downloading economic data for week of {week_id}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse CSV content
        if "text/csv" in response.headers.get("content-type", ""):
            # Save raw CSV response
            raw_filename = f"data/crawled/fxstreet_{week_id}_raw.csv"
            with open(raw_filename, "wb") as f:
                f.write(response.content)
            
            # Parse CSV to JSON format
            events = parse_fxstreet_csv(response.content.decode('utf-8'))
        else:
            # Handle JSON response if API returns JSON instead of CSV
            events = response.json()
        
        # Save events to JSON file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
        
        print(f"✅ Data saved to: {filename}")
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        # If download fails but we already have data, don't overwrite it
        
    return filename

def parse_fxstreet_csv(csv_content):
    """Parse CSV content to structured JSON format"""
    # Use StringIO to parse the CSV content without saving to disk
    from io import StringIO
    df = pd.read_csv(StringIO(csv_content))
    events = []

    for _, row in df.iterrows():
        start_str = row["Start"]
        dt = datetime.strptime(start_str, "%m/%d/%Y %H:%M:%S")

        events.append({
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "currency": row["Currency"],
            "event": row["Name"],
            "impact": row["Impact"].lower(),
            "actual": "",
            "forecast": "",
            "previous": "",
            "market_reaction": ""
        })
    
    return events

def load_json_events(week_id):
    """Load events from cached JSON file"""
    filename = f"data/crawled/fxstreet_{week_id}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading cached data: {e}")
        return []

def download_fxstreet_csv_authenticated():
    """Legacy function for backward compatibility"""
    start, end = get_current_week_range()
    week_id = start.strftime("%Y-%m-%d")
    
    events = get_fxstreet_events(period="week", force_refresh=True)
    
    return f"data/crawled/fxstreet_{week_id}.json"

def parse_fxstreet_csv_to_json(filepath=None):
    """Legacy function for backward compatibility"""
    start, end = get_current_week_range()
    week_id = start.strftime("%Y-%m-%d")
    
    # If we already have the JSON file, load it
    if json_exists(week_id):
        return load_json_events(week_id)
    
    # Otherwise, if a filepath was provided, parse it
    if filepath and os.path.exists(filepath):
        df = pd.read_csv(filepath)
        events = []

        for _, row in df.iterrows():
            start_str = row["Start"]
            dt = datetime.strptime(start_str, "%m/%d/%Y %H:%M:%S")

            events.append({
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M"),
                "currency": row["Currency"],
                "event": row["Name"],
                "impact": row["Impact"].lower(),
                "actual": "",
                "forecast": "",
                "previous": "",
                "market_reaction": ""
            })

        filename = f"data/crawled/fxstreet_{week_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)

        return events
    
    # If no file exists and none provided, return empty list
    return []

def parse_fxstreet_csv(csv_content):
    """Parse CSV content to structured JSON format"""
    # Use StringIO to parse the CSV content without saving to disk
    from io import StringIO
    df = pd.read_csv(StringIO(csv_content))
    events = []

    for _, row in df.iterrows():
        start_str = row["Start"]
        dt = datetime.strptime(start_str, "%m/%d/%Y %H:%M:%S")

        events.append({
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "currency": row["Currency"],
            "event": row["Name"],
            "impact": row["Impact"].lower(),
            "actual": "",
            "forecast": "",
            "previous": "",
            "market_reaction": ""
        })
    
    return events

def load_json_events(week_id):
    """Load events from cached JSON file"""
    filename = f"data/crawled/fxstreet_{week_id}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading cached data: {e}")
        return []

def get_current_week_range():
    today = datetime.now(timezone.utc)
    start = today - timedelta(days=today.weekday())  # Monday
    end = start + timedelta(days=6)  # Sunday
    return start, end

def get_next_week_range():
    today = datetime.now(timezone.utc)
    start = today + timedelta(days=(7 - today.weekday()))  # Next Monday
    end = start + timedelta(days=6)  # Sunday
    return start, end

def format_date_range(start, end):
    return (
        start.strftime("%Y-%m-%dT00:00:00Z"),
        end.strftime("%Y-%m-%dT23:59:59Z")
    )

def build_fxstreet_url(from_date, to_date):
    base_url = "https://calendar-api.fxsstatic.com/en/api/v1/eventDates"
    categories = [
        "8896AA26-A50C-4F8B-AA11-8B3FCCDA1DFD", "FA6570F6-E494-4563-A363-00D0F2ABEC37",
        "C94405B5-5F85-4397-AB11-002A481C4B92", "E229C890-80FC-40F3-B6F4-B658F3A02635",
        "24127F3B-EDCE-4DC4-AFDF-0B3BD8A964BE", "DD332FD3-6996-41BE-8C41-33F277074FA7",
        "7DFAEF86-C3FE-4E76-9421-8958CC2F9A0D", "1E06A304-FAC6-440C-9CED-9225A6277A55",
        "33303F5E-1E3C-4016-AB2D-AC87E98F57CA", "9C4A731A-D993-4D55-89F3-DC707CC1D596",
        "91DA97BD-D94A-4CE8-A02B-B96EE2944E4C", "E9E957EC-2927-4A77-AE0C-F5E4B5807C16"
    ]

    categories_params = "".join([f"&categories={cat}" for cat in categories])
    url = f"{base_url}/{from_date}/{to_date}?volatilities=HIGH&countries=US&countries=EMU{categories_params}"
    return url

def json_exists(for_week: str):
    filename = f"data/crawled/fxstreet_{for_week}.json"
    return os.path.exists(filename)

def get_random_headers():
    return {
        "accept": "text/csv",
        "origin": "https://www.fxstreet.com",
        "referer": "https://www.fxstreet.com/",
        "user-agent": random.choice(USER_AGENTS)
    }

def filter_events_by_date(events, date_str=None):
    """
    Filter events by specific date
    
    Args:
        events (list): List of event dictionaries
        date_str (str): Date string in YYYY-MM-DD format or None for today
    
    Returns:
        list: Filtered list of events
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    return [event for event in events if event.get("date") == date_str]
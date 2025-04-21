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

def download_fxstreet_csv_authenticated():
    start, end = get_current_week_range()
    from_date, to_date = format_date_range(start, end)
    url = build_fxstreet_url(from_date, to_date)

    week_id = start.strftime("%Y-%m-%d")  # e.g. "2025-04-22"
    if json_exists(week_id):
        print(f"✅ Data for week starting {week_id} already exists. Skipping download.")
    else:
    
        #url = "https://calendar-api.fxsstatic.com/en/api/v1/eventDates/2025-04-21T19:10:38Z/2025-04-23T21:10:38Z?&volatilities=HIGH&countries=US&countries=EMU&categories=8896AA26-A50C-4F8B-AA11-8B3FCCDA1DFD&categories=FA6570F6-E494-4563-A363-00D0F2ABEC37&categories=C94405B5-5F85-4397-AB11-002A481C4B92&categories=E229C890-80FC-40F3-B6F4-B658F3A02635&categories=24127F3B-EDCE-4DC4-AFDF-0B3BD8A964BE&categories=DD332FD3-6996-41BE-8C41-33F277074FA7&categories=7DFAEF86-C3FE-4E76-9421-8958CC2F9A0D&categories=1E06A304-FAC6-440C-9CED-9225A6277A55&categories=33303F5E-1E3C-4016-AB2D-AC87E98F57CA&categories=9C4A731A-D993-4D55-89F3-DC707CC1D596&categories=91DA97BD-D94A-4CE8-A02B-B96EE2944E4C&categories=E9E957EC-2927-4A77-AE0C-F5E4B5807C16"

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
        filename = "fxstreet_{week_id}.json" # <- TODO save the file with week_id in it

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        with open(filename, "wb") as f:
            f.write(response.content)

        print(f"✅ CSV saved to: {filename}")
        return filename


def parse_fxstreet_csv_to_json(filepath="data/crawled/calendar-event-list.csv"):
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

    with open("data/crawled/fxstreet_events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)

    return events

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
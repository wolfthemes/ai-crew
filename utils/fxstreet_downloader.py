# utils/fxstreet_downloader.py
import json
import requests
import pandas as pd
from datetime import datetime
from io import StringIO

def download_fxstreet_csv_authenticated():
    url = "https://calendar-api.fxsstatic.com/en/api/v1/eventDates/2025-04-21T19:10:38Z/2025-04-23T21:10:38Z?&volatilities=HIGH&countries=US&countries=EMU&categories=8896AA26-A50C-4F8B-AA11-8B3FCCDA1DFD&categories=FA6570F6-E494-4563-A363-00D0F2ABEC37&categories=C94405B5-5F85-4397-AB11-002A481C4B92&categories=E229C890-80FC-40F3-B6F4-B658F3A02635&categories=24127F3B-EDCE-4DC4-AFDF-0B3BD8A964BE&categories=DD332FD3-6996-41BE-8C41-33F277074FA7&categories=7DFAEF86-C3FE-4E76-9421-8958CC2F9A0D&categories=1E06A304-FAC6-440C-9CED-9225A6277A55&categories=33303F5E-1E3C-4016-AB2D-AC87E98F57CA&categories=9C4A731A-D993-4D55-89F3-DC707CC1D596&categories=91DA97BD-D94A-4CE8-A02B-B96EE2944E4C&categories=E9E957EC-2927-4A77-AE0C-F5E4B5807C16"

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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    filename = "calendar-event-list.csv"
    cd = response.headers.get("Content-Disposition", "")
    if "filename=" in cd:
        filename = cd.split("filename=")[-1].strip('"')

    with open(filename, "wb") as f:
        f.write(response.content)

    print(f"✅ CSV downloaded: {filename}")
    return filename


def parse_fxstreet_csv_to_json(filepath="calendar-event-list.csv"):
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
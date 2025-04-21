import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_downloader import download_fxstreet_csv_authenticated, parse_fxstreet_csv_to_json
from datetime import datetime, timedelta, UTC

# Generate date range for the week
today = datetime.now(UTC)
start_date = today.strftime("%Y-%m-%dT00:00:00")
end_date = (today + timedelta(days=6)).strftime("%Y-%m-%dT23:59:59")

# Download and parse
csv_data = download_fxstreet_csv_authenticated()
events = parse_fxstreet_csv_to_json()

from pprint import pprint
pprint(events[:3])

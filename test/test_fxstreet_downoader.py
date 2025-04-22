import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.fxstreet_events_downloader import get_fxstreet_events
from datetime import datetime, timedelta, UTC

# Generate date range for the week
today = datetime.now(UTC)
start_date = today.strftime("%Y-%m-%dT00:00:00")
end_date = (today + timedelta(days=6)).strftime("%Y-%m-%dT23:59:59")

# Download and parse (with force_refresh=True to ensure we get new data)
events = get_fxstreet_events()

from pprint import pprint
pprint(events)
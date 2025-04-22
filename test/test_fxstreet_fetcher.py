import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.fxstreet_fetcher import FetchFXStreetNews

# Create the tool
fx_tool = FetchFXStreetNews()

# Get weekly report
weekly_data = fx_tool._run(
    currency_pair="EUR/USD",
    impact_level="high",
    report_type="weekly"
)

print( weekly_data )
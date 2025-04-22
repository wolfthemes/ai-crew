import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from crews.market_crew import run_market_analysis
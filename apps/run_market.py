from pathlib import Path
import sys
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from crews.market_crew import run_market_analysis

if __name__ == "__main__":
    result = run_market_analysis(verbose=True)
    if result:
        print(result)
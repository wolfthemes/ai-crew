# test_logging.py
import sys
import os
from pathlib import Path
from datetime import date

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.helpers import setup_logging

def test_loggin():

    print("🔄 Whatever...")
    logger = setup_logging()
    today = date.today().strftime("%Y-%m-%d")
    logger.info(f"Starting test logging {today}")

if __name__ == "__main__":
    test_loggin()
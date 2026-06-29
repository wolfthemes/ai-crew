#!/bin/bash
cd /mnt/c/Users/Constantin/dev/ai-crew
source .venv/bin/activate
python scripts/post_economic_events_to_notion.py
python scripts/generate_market_report.py
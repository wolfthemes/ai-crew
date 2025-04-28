@echo off
cd %USERPROFILE%\wolfthemes-dev\ai-crew
call .venv\Scripts\activate.bat
python scripts\post_economic_events_to_notion.py
python scripts\generate_market_report.py
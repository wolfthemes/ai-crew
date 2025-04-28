@echo off
cd %USERPROFILE%\wolfthemes-dev\ai-crew
call .venv\Scripts\activate.bat
python scripts\generate_reply_drafts.py
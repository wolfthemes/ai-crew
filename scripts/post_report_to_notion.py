# scripts/post_report_to_notion.py

import os
import sys
from pathlib import Path
from datetime import date
import argparse

# Add the parent directory to sys.path
current_file = Path(__file__).resolve()
parent_directory = current_file.parents[1]
sys.path.append(str(parent_directory))

from tools.notion_writer import PostToNotion
from dotenv import load_dotenv

def post_report_to_notion(file_path=None, title=None):
    """Post an existing report to Notion"""
    load_dotenv()
    
    # Verify environment variables
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_db_key = os.getenv("NOTION_MARKET_REPORTS_DB_KEY")
    
    if not notion_api_key or not notion_db_key:
        print("❌ Notion environment variables not set")
        return False
    
    # Default to the latest report if no file path is specified
    if not file_path:
        today = date.today().strftime("%Y-%m-%d")
        file_path = f"data/reports/eurusd_weekly_report_{today}.md"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"❌ Report file not found: {file_path}")
        return False
    
    # Read the report content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        print(f"✅ Successfully read report ({len(report_content)} characters)")
    except Exception as e:
        print(f"❌ Error reading report file: {str(e)}")
        return False
    
    # Initialize the Notion tool
    notion_tool = PostToNotion()
    
    # Get title from the report if not specified
    if not title:
        lines = report_content.split('\n')
        if lines and lines[0].startswith('# '):
            title = lines[0][2:].strip()
        else:
            title = f"EUR/USD Weekly Report – {date.today().strftime('%Y-%m-%d')}"
    
    # Post to Notion
    print(f"📝 Posting to Notion with title: {title}")
    result = notion_tool._run(content=report_content, title=title)
    
    print(f"\nResult: {result}")
    return "SUCCESS" in result

def main():
    parser = argparse.ArgumentParser(description="Post an existing report to Notion")
    parser.add_argument("--file", "-f", help="Path to the report file")
    parser.add_argument("--title", "-t", help="Custom title for the report")
    
    args = parser.parse_args()
    
    success = post_report_to_notion(args.file, args.title)
    print(f"\nOperation {'succeeded' if success else 'failed'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
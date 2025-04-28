# test_notion_post.py
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
from dotenv import load_dotenv
from tools.notion_writer import PostToNotion

def test_notion_posting():
    """
    Test posting an existing report to Notion
    """
    # Load environment variables
    load_dotenv()
    
    # Verify environment variables are set
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_db_key = os.getenv("NOTION_MARKET_REPORTS_DB_KEY")
    
    print("Notion environment variables check:")
    if notion_api_key:
        print(f"✅ NOTION_API_KEY is set (starts with: {notion_api_key[:4]}...)")
    else:
        print("❌ NOTION_API_KEY is NOT set")
        return False
    
    if notion_db_key:
        print(f"✅ NOTION_MARKET_REPORTS_DB_KEY is set (starts with: {notion_db_key[:4]}...)")
    else:
        print("❌ NOTION_MARKET_REPORTS_DB_KEY is NOT set")
        return False
    
    # Path to the report file
    report_path = "data/reports/eurusd_weekly_report_2025-04-28.md"
    
    # Check if the file exists
    if not os.path.exists(report_path):
        print(f"❌ Report file not found: {report_path}")
        return False
    
    print(f"✅ Found report file: {report_path}")
    
    # Read the report content
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        print(f"✅ Successfully read report content ({len(report_content)} characters)")
    except Exception as e:
        print(f"❌ Error reading report file: {str(e)}")
        return False
    
    # Initialize the Notion tool
    try:
        notion_tool = PostToNotion()
        print("✅ PostToNotion tool initialized")
    except Exception as e:
        print(f"❌ Error initializing PostToNotion tool: {str(e)}")
        return False
    
    # Post to Notion
    print("\nAttempting to post to Notion...")
    try:
        result = notion_tool._run(
            content=report_content,
            title="EUR/USD Weekly Report - TEST POST",
            date_str="2025-04-22",
            period="weekly"
        )
        
        print(f"\nResult: {result}")
        
        if "SUCCESS" in result:
            print("\n✅ Successfully posted to Notion!")
            return True
        else:
            print("\n❌ Failed to post to Notion")
            return False
    except Exception as e:
        print(f"\n❌ Exception while posting to Notion: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_notion_posting()
    print(f"\nTest {'passed' if success else 'failed'}")
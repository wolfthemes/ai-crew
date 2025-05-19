import os
import sys
import re
import argparse
from pathlib import Path
import logging
from datetime import date, datetime
import pytz

# Add the parent directory to sys.path
current_file = Path(__file__).resolve()
parent_directory = current_file.parents[1]
sys.path.append(str(parent_directory))

from utils.helpers import setup_logging, clean_markdown_content
from dotenv import load_dotenv

logger = setup_logging()
today = date.today().strftime("%Y-%m-%d")

def extract_summary_from_report(report_content):
    """
    Extract a summary from the report content.
    Attempt to find a summary section or the first paragraph.
    """
    # Try to find a summary section
    summary_match = re.search(r'#+ (?:Summary|Executive Summary|Overview).*?\n(.*?)(?:\n#+|\Z)', 
                              report_content, re.DOTALL | re.IGNORECASE)
    
    if summary_match:
        # Extract first paragraph of summary section
        summary_text = summary_match.group(1).strip()
        first_para = summary_text.split('\n\n')[0].strip()
        # Remove any markdown formatting
        clean_summary = re.sub(r'\*\*|\*|_|`|#', '', first_para)
        # Limit to a reasonable length
        return clean_summary[:200] + ('...' if len(clean_summary) > 200 else '')
    
    # If no summary section found, take first paragraph of the report
    first_para_match = re.search(r'^(?:#.*?\n+)?(.*?)(?:\n\n|\Z)', report_content, re.DOTALL)
    if first_para_match:
        first_para = first_para_match.group(1).strip()
        clean_summary = re.sub(r'\*\*|\*|_|`|#', '', first_para)
        return clean_summary[:200] + ('...' if len(clean_summary) > 200 else '')
    
    return "No summary available"

def save_to_obsidian(file_path=None, content=None, title=None, period=None, report_date=None):
    """
    Saves a markdown report file to the Obsidian vault.
    
    Args:
        file_path (str): Path to the markdown file to save to Obsidian
        content (str): Direct content to save (used instead of file_path if provided)
        title (str, optional): Title for the report. If None, will use filename.
        period (str, optional): "daily" or "weekly" report period
        report_date (date, optional): Date for the report. If None, will use current date or parse from filename.
        
    Returns:
        bool: True if saving was successful, False otherwise
    """
    load_dotenv()
    
    # Verify environment variables
    obsidian_dir = os.getenv("OBSIDIAN_DIR")
    
    if not obsidian_dir:
        logger.error("❌ OBSIDIAN_DIR environment variable not set")
        return False
    
    logger.info(f"Using Obsidian directory: {obsidian_dir}")
    
    # Get content either from the provided string or from file
    report_content = None
    
    if content is not None:
        report_content = clean_markdown_content(content)
        logger.info(f"Using provided content ({len(report_content)} characters)")
    elif file_path:
        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"❌ Report file not found: {file_path}")
            return False
        
        # Read the report content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            report_content = clean_markdown_content(report_content)
            logger.info(f"✅ Successfully read report from file ({len(report_content)} characters)")
        except Exception as e:
            logger.error(f"❌ Error reading report file: {str(e)}")
            return False
    else:
        logger.error("❌ Either file_path or content must be provided")
        return False
    
    # Determine the period based on the file path if not specified
    if not period:
        if file_path and "daily" in file_path.lower():
            period = "daily"
        else:
            period = "weekly"  # Default
    
    # Determine the report date if not specified
    if not report_date:
        # Try to parse date from filename if available
        if file_path:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_path)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    # Use current date if parsing fails
                    report_date = date.today()
            else:
                # Use current date if no date in filename
                report_date = date.today()
        else:
            # Use current date if no file_path
            report_date = date.today()
    
    # Format the date
    date_str = report_date.strftime("%Y-%m-%d")
    
    # Create the filename according to the required format
    if title:
        # If title is provided, use it directly
        filename = f"{title}.md"
    else:
        # Default filename format
        filename = f"EU {period.capitalize()} Report {date_str}.md"
    
    # Determine subfolder
    folder_name = "Daily" if period == "daily" else "Weekly"
    
    try:
        # Build the directory path using Path for better cross-platform compatibility
        target_dir = Path(obsidian_dir) / "Market Reports" / folder_name
        
        # Ensure the directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Confirmed directory: {target_dir}")
        
        # Build the full file path
        target_file = target_dir / filename
        logger.info(f"🔍 Target file path: {target_file}")
        
        # Extract a summary from the report
        summary = extract_summary_from_report(report_content)
        
        # Create the metadata section
        metadata = f"""---
area: trading
date: {date_str}
type: report
journal: "[[Market Reports]]"
period: {period}
summary: "{summary}"
---

"""
        # Combine metadata and report content
        full_content = metadata + report_content
        
        # Write to file
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        logger.info(f"📝 Report saved to Obsidian at {target_file}")
        return True
    
    except Exception as e:
        import traceback
        logger.error(f"❌ Error saving to Obsidian: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Save a market report to Obsidian vault")
    parser.add_argument("--file", "-f", help="Path to the report file")
    parser.add_argument("--title", "-t", help="Custom title for the report file (without extension)")
    parser.add_argument("--period", "-p", choices=["daily", "weekly"], 
                        help="Report period (daily or weekly)")
    parser.add_argument("--date", "-d", help="Report date in YYYY-MM-DD format (defaults to current date)")
    parser.add_argument("--content", "-c", help="Direct content to save instead of reading from file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with detailed logging")
    
    args = parser.parse_args()
    
    # Configure logging level if debug mode requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse date if provided
    report_date = None
    if args.date:
        try:
            report_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid date format: {args.date}. Expected format: YYYY-MM-DD")
            return 1
    
    # Run the function
    success = save_to_obsidian(
        file_path=args.file,
        content=args.content,
        title=args.title,
        period=args.period,
        report_date=report_date
    )
    
    print(f"\nOperation {'succeeded' if success else 'failed'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
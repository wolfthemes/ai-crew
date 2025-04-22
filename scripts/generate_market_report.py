#!/usr/bin/env python3
"""
Generate EUR/USD Market Report

This script runs the market analysis crew to generate either a daily or
weekly EUR/USD market report and optionally posts it to Notion.
"""

import sys
import argparse
from pathlib import Path
import logging
from datetime import date

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from crews.market_crew import run_market_analysis

def setup_logging():
    """Set up basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Run the market analysis with command line arguments"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate EUR/USD market report")
    parser.add_argument("--period", choices=["daily", "weekly"], default="weekly",
                        help="Report period (daily or weekly)")
    parser.add_argument("--no-notion", action="store_true", 
                        help="Skip posting to Notion")
    parser.add_argument("--no-save", action="store_true",
                        help="Skip saving report to file")
    parser.add_argument("--quiet", action="store_true",
                        help="Run in quiet mode (less verbose output)")
    
    args = parser.parse_args()
    
    setup_logging()
    
    today = date.today().strftime("%Y-%m-%d")
    logging.info(f"Starting EUR/USD {args.period} report generation for {today}")
    
    # Run the market analysis with command line options
    result = run_market_analysis(
        verbose=not args.quiet,
        post_to_notion=not args.no_notion,
        save_to_file=not args.no_save,
        period=args.period
    )
    
    if result:
        logging.info(f"{args.period.capitalize()} report generation completed successfully")
        return 0
    else:
        logging.error(f"{args.period.capitalize()} report generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
EUR/USD Market Analysis Generator

This script runs a CrewAI-powered market analysis to generate comprehensive
EUR/USD weekly reports with technical, fundamental, and sentiment analysis.
"""

import os
import argparse
from pathlib import Path
import sys

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from crews.market_crew import run_market_analysis
from datetime import date

def main():
    """Run the market analysis with command line arguments"""
    parser = argparse.ArgumentParser(description="Generate EUR/USD Market Analysis")
    parser.add_argument("--no-notion", action="store_true", 
                        help="Skip posting to Notion")
    parser.add_argument("--quiet", action="store_true", 
                        help="Run in quiet mode (less verbose output)")
    parser.add_argument("--save", action="store_true",
                        help="Save report to a markdown file")
    
    args = parser.parse_args()
    
    print("\n")
    print("="*70)
    print("🚀 STARTING EUR/USD MARKET ANALYSIS".center(70))
    print("="*70)
    print("\n")
    
    # Run the market analysis with specified options
    report = run_market_analysis(
        verbose=not args.quiet,
        post_to_notion=not args.no_notion,
        save_to_file=args.save
    )
    
    if report:
        # Convert CrewOutput to string
        report_text = str(report)
        
        # Calculate report statistics
        word_count = len(report_text.split())
        char_count = len(report_text)
        
        print("\n")
        print("="*70)
        print("✅ REPORT GENERATION COMPLETE".center(70))
        print("="*70)
        print(f"📊 Report Statistics:".center(70))
        print(f"   - Word Count: {word_count}".center(70))
        print(f"   - Character Count: {char_count}".center(70))
        
        today = date.today().strftime("%Y-%m-%d")
        
        # Always save the report if requested via command line
        if args.save:
            reports_dir = Path("data/reports")
            reports_dir.mkdir(exist_ok=True)
            
            file_path = reports_dir / f"eurusd_weekly_report_{today}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            
            print(f"📄 Report saved to: {file_path}".center(70))
        
        print("="*70)
        print("\n")
        return 0
    else:
        print("\n")
        print("="*70)
        print("❌ FAILED TO GENERATE REPORT".center(70))
        print("="*70)
        print("\n")
        return 1

if __name__ == "__main__":
    exit(main())
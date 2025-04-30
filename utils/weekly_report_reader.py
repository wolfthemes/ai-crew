import os
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from typing import Optional, Dict, Any

class WeeklyReportReader:
    """
    Utility class to read and provide access to the most recent weekly report
    for reference in daily reports.
    """
    
    def __init__(self, reports_dir: str = "data/reports/weekly"):
        """
        Initialize with the directory containing weekly reports.
        
        Args:
            reports_dir: Path to the directory containing weekly reports
        """
        self.reports_dir = Path(reports_dir)
    
    def get_most_recent_report(self) -> Optional[str]:
        """
        Find and return the content of the most recent weekly report.
        
        Returns:
            str: Content of the most recent weekly report, or None if not found
        """
        if not self.reports_dir.exists():
            return None
            
        # Get all weekly report files
        weekly_reports = list(self.reports_dir.glob("eurusd_weekly_report_*.md"))
        
        if not weekly_reports:
            return None
            
        # Sort by filename date (most recent last)
        weekly_reports.sort()
        most_recent_report_path = weekly_reports[-1]
        
        # Read the content
        try:
            with open(most_recent_report_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading weekly report: {e}")
            return None
    
    def get_weekly_report_metadata(self) -> Dict[str, Any]:
        """
        Extract key metadata from the most recent weekly report.
        
        Returns:
            Dict with key weekly outlook information:
            - fundamental_outlook: str
            - technical_bias: str
            - key_levels: Dict[str, float]
            - report_date: str
        """
        report_content = self.get_most_recent_report()
        
        if not report_content:
            return {
                "fundamental_outlook": "No weekly report available",
                "technical_bias": "Unknown",
                "key_levels": {},
                "report_date": "Unknown"
            }
        
        # Extract report date from filename
        weekly_reports = list(self.reports_dir.glob("eurusd_weekly_report_*.md"))
        if weekly_reports:
            # Sort by filename date (most recent last)
            weekly_reports.sort()
            most_recent_report_path = weekly_reports[-1]
            filename = most_recent_report_path.name
            # Extract date from filename format "eurusd_weekly_report_YYYY-MM-DD.md"
            try:
                report_date = filename.split("_")[-1].replace(".md", "")
            except:
                report_date = "Unknown"
        else:
            report_date = "Unknown"
        
        # Basic parsing of the report to extract key information
        # This is a simplified approach - a more sophisticated parser could be implemented
        lines = report_content.split("\n")
        
        fundamental_outlook = "No fundamental outlook found in weekly report"
        technical_bias = "Unknown"
        key_levels = {}
        
        # Simple parsing by section headers
        current_section = None
        section_content = []
        
        for line in lines:
            if line.startswith("## ") or line.startswith("# "):
                # Save previous section
                if current_section == "Fundamental Outlook" and section_content:
                    fundamental_outlook = " ".join(section_content)
                elif current_section == "Technical Analysis" and section_content:
                    # Try to extract bias from technical section
                    technical_section = " ".join(section_content)
                    if "bullish" in technical_section.lower():
                        technical_bias = "Bullish"
                    elif "bearish" in technical_section.lower():
                        technical_bias = "Bearish"
                    elif "neutral" in technical_section.lower():
                        technical_bias = "Neutral"
                
                # Start new section
                current_section = line.replace("#", "").strip()
                section_content = []
            elif current_section and line.strip():
                section_content.append(line.strip())
        
        # Try to extract key levels from the content
        for line in lines:
            # Look for common key level patterns
            if "support" in line.lower() and ":" in line:
                try:
                    level = float(line.split(":")[-1].strip())
                    key_levels["support"] = level
                except:
                    pass
            elif "resistance" in line.lower() and ":" in line:
                try:
                    level = float(line.split(":")[-1].strip())
                    key_levels["resistance"] = level
                except:
                    pass
        
        return {
            "fundamental_outlook": fundamental_outlook,
            "technical_bias": technical_bias,
            "key_levels": key_levels,
            "report_date": report_date
        }
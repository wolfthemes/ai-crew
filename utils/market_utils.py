from datetime import datetime, date
import pytz
from typing import List, Dict, Any
import re

def is_tradable_day(current_date: date = None, economic_events: List[Dict[str, Any]] = None) -> bool:
    """
    Determines if the current day is a tradable day based on:
    1. Day of the week (only Tuesday, Wednesday, Thursday)
    2. Absence of high-impact news events on the current date
    
    Args:
        current_date: The date to check (defaults to today)
        economic_events: List of economic events from FXStreet
        
    Returns:
        bool: True if the day is tradable, False otherwise
    """
    # Use current date if none provided
    if current_date is None:
        paris_tz = pytz.timezone('Europe/Paris')
        current_date = datetime.now(paris_tz).date()
    
    # Check day of week (1 = Monday, 7 = Sunday)
    day_of_week = current_date.isoweekday()
    
    # Only Tuesday (2), Wednesday (3), Thursday (4) are tradable
    if day_of_week not in [2, 3, 4]:
        return False
    
    # If no economic events data provided, assume tradable
    if economic_events is None:
        return True
    
    # Check for high-impact news on the current date
    current_date_str = current_date.strftime("%Y-%m-%d")
    
    keywords = [r'President.*Speech', r'ECB.*Speech', r'ECB.*Speech', r'Fed.*Speech', r'Nonfarm.*Payrolls', r'Consumer.*Prices', r'Fed.*Interest.*Rate', r'FOMC.*Press.*Conference']
    pattern = re.compile('|'.join(re.escape(k) for k in keywords), re.IGNORECASE)

    high_impact_events = [
        event for event in economic_events 
        if (
            event.get("date") == current_date_str
            and event.get("impact", "").lower() == "high"
            and pattern.search(event.get("event", ""))
        )
    ]
    
    # If there are high-impact events, the day is not tradable
    return len(high_impact_events) == 0
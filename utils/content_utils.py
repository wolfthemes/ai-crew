# utils/content_utils.py
from datetime import datetime, timedelta
import json

def load_theme_data():
    """Load theme data from JSON file"""
    try:
        with open('data/themes/theme_catalog.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def format_category(category):
    """Format category text properly"""
    if isinstance(category, list):
        if len(category) == 1:
            return category[0]
        elif len(category) == 2:
            return f"{category[0]} and {category[1]}"
        else:
            return ", ".join(category[:-1]) + f", and {category[-1]}"
    return category if category else "WordPress"

def format_hashtags(category):
    """Format category for hashtags"""
    if isinstance(category, list):
        return " ".join([f"#{cat.replace(' ', '')}" for cat in category])
    elif category:
        return f"#{category.replace(' ', '')}"
    return "#WordPress"


def is_new_theme(theme):
    """Determine if a theme is new based on version and update date"""
    version = theme.get("version", "1.0.0")
    updated = theme.get("updated", "")
    
    # Check if version is below 1.5 (relatively new)
    is_early_version = version.startswith("1.0") or version.startswith("1.1")
    
    # Check if updated within last 3 months
    if updated:
        try:
            updated_date = datetime.strptime(updated, "%Y-%m-%d")
            today = datetime.now()
            days_since_update = (today - updated_date).days
            recently_updated = days_since_update < 90
        except ValueError:
            recently_updated = False
    else:
        recently_updated = False
    
    return is_early_version or recently_updated

def get_random_feature(features_list, max_length=100):
    """Get a random feature from the list
    
    Args:
        features_list (list): List of features
        max_length (int): Maximum length of feature text
        
    Returns:
        str: Selected feature or empty string if none
    """
    if not features_list:
        return ""
        
    # Filter out empty features
    valid_features = [f for f in features_list if f]
    
    if not valid_features:
        return ""
        
    # Select a random feature
    import random
    feature = random.choice(valid_features)
    
    # Trim if needed
    if len(feature) > max_length:
        feature = feature[:max_length-3] + "..."
        
    return feature

def format_list_to_text(items_list):
    """Format a list of items into readable text
    
    Args:
        items_list (list): List of strings to format
        
    Returns:
        str: Formatted text
    """
    if not items_list:
        return ""
        
    # Remove any empty items
    items = [item for item in items_list if item]
    
    if not items:
        return ""
        
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return ", ".join(items[:-1]) + f", and {items[-1]}"
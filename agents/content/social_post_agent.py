# agents/content/social_post_agent.py

import json
import random
import os
from datetime import datetime

def load_data():
    """Load data required for social post generation"""
    data = {
        "templates": {},
        "theme_data": {},
        "categories": {}
    }
    
    # Load content templates
    try:
        with open('data/themes/content_templates.json', 'r') as f:
            data["templates"] = json.load(f)
    except FileNotFoundError:
        # Create basic templates if file doesn't exist
        data["templates"] = {
            "social_posts": {
                "facebook": [
                    "Check out {theme_name}, our {category} WordPress theme: {demourl}",
                    "Looking for a {category} theme? Try {theme_name}: {demourl}"
                ],
                "instagram": [
                    "{theme_name} - Premium {category} WordPress theme\n\n#WordPress #{category}",
                    "Introducing {theme_name} for {category} websites\n\n#WebDesign #WordPress"
                ],
                "x": [
                    "{theme_name}: Professional {category} WordPress theme. See demo: {shortlink}",
                    "Just launched: {theme_name} for {category} websites. {shortlink}"
                ]
            }
        }
        # Save the basic templates
        os.makedirs('data/themes', exist_ok=True)
        with open('data/themes/content_templates.json', 'w') as f:
            json.dump(data["templates"], f, indent=2)
    
    # Load theme data
    try:
        with open('data/themes/theme_catalog.json', 'r') as f:
            data["theme_data"] = json.load(f)
    except FileNotFoundError:
        print("Theme catalog not found. Please ensure theme_catalog.json exists.")
    
    # Load categories (optional for basic function)
    try:
        with open('data/themes/theme_categories.json', 'r') as f:
            data["categories"] = json.load(f)
    except FileNotFoundError:
        # Will function without categories, just less specific
        pass
        
    return data

def generate_posts(theme_slug, platforms=None, count=1, data=None):
    """Generate social media posts for a theme
    
    Args:
        theme_slug (str): The theme's slug
        platforms (list): List of platforms to generate for ['facebook', 'instagram', 'x']
        count (int): Number of posts per platform
        data (dict): Optional pre-loaded data
        
    Returns:
        dict: Dictionary of platform -> list of posts
    """
    if platforms is None:
        platforms = ['facebook', 'instagram', 'x']
    
    # Load data if not provided
    if data is None:
        data = load_data()
    
    # Get theme data
    theme = data["theme_data"].get(theme_slug)
    if not theme:
        return {"error": f"Theme '{theme_slug}' not found"}
    
    # Prepare context for template filling
    ctx = {
        "theme_name": theme.get("name", ""),
        "category": theme.get("category", "WordPress"),
        "subcategory": "",  # Could be enhanced later
        "builder": theme.get("builder", ""),
        "demourl": theme.get("demourl", ""),
        "shortlink": theme.get("shortlink", ""),
        "url": theme.get("url", ""),
        "version": theme.get("version", ""),
        "updated": theme.get("updated", "")
    }
    
    # Generate posts for each platform
    results = {}
    
    for platform in platforms:
        platform_templates = data["templates"].get("social_posts", {}).get(platform, [])
        if not platform_templates:
            results[platform] = [f"Check out our {ctx['theme_name']} theme! {ctx['demourl']}"]
            continue
        
        # Select random templates
        selected_templates = random.sample(
            platform_templates, 
            min(count, len(platform_templates))
        )
        
        # Fill in the templates
        posts = []
        for template in selected_templates:
            try:
                post = template.format(**ctx)
                posts.append(post)
            except KeyError as e:
                # Handle missing keys in template
                posts.append(f"Check out {ctx['theme_name']}! {ctx['demourl']}")
        
        results[platform] = posts
    
    return results
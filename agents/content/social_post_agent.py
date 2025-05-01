# agents/content/social_post_agent.py

import json
import random
import os
from datetime import datetime

from utils.content_utils import format_hashtags, format_list_to_text, get_random_feature, is_new_theme, format_category

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
                    "Check out {theme_name}, our {category_text} WordPress theme: {demourl}",
                    "Looking for a {category_text} theme? Try {theme_name}: {demourl}"
                ],
                "instagram": [
                    "{theme_name} - Premium {category_text} WordPress theme\n\n#WordPress #{category_hashtags}",
                    "Introducing {theme_name} for {category_text} websites\n\n#WebDesign #WordPress"
                ],
                "x": [
                    "{theme_name}: Professional {category_text} WordPress theme. See demo: {shortlink}",
                    "Just launched: {theme_name} for {category_text} websites. {shortlink}"
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

def get_theme_templates(theme, platform, data):
    """Get appropriate templates based on theme characteristics"""
    # Get base templates
    all_templates = data["templates"].get("social_posts", {}).get(platform, [])
    
    # Check if this theme has specific target audiences or styles that warrant custom templates
    target_audience = theme.get("target_audience", [])
    theme_style = theme.get("theme_style", [])
    
    # Custom templates for photographers
    if platform == "instagram" and any("Photographer" in audience for audience in target_audience):
        photo_templates = [
            "Photographers! Elevate your portfolio with {theme_name}, designed for showcasing your work beautifully ✨\n\n#Photography #{category_hashtags} #PhotographyWebsite",
            "Calling all photographers! {theme_name} is the perfect WordPress theme to display your visual stories ✨\n\n#PhotographyPortfolio #{category_hashtags}",
            "{theme_name}: A {theme_style} WordPress theme crafted for professional photographers 📸\n\n#Photography #{category_hashtags}"
        ]
        return photo_templates
        
    # Custom templates for musicians
    elif platform == "facebook" and any("Music" in cat for cat in ([theme.get("category", "")] if isinstance(theme.get("category", ""), str) else theme.get("category", []))):
        music_templates = [
            "Musicians! {theme_name} showcases your tracks, events and videos perfectly. Our {category_text} WordPress theme includes everything you need: {key_feature}. See the demo: {demourl}",
            "Create a professional music website with {theme_name}. Perfect for {target_audience}, with built-in features for tracks, albums and events. Check it out: {demourl}",
            "Introducing {theme_name}: A {theme_style} WordPress theme for musicians and bands. Key feature: {key_feature}. Preview: {demourl}"
        ]
        return music_templates
    
    # Regular template selection based on whether theme is new or established
    if is_new_theme(theme):
        # Templates for new themes
        if platform == "facebook":
            return [
                "Just launched: {theme_name}, a new {category_text} WordPress theme built with {builder}. Check out the demo: {demourl}",
                "Introducing {theme_name} - our latest {category_text} WordPress theme with stunning design and powerful features. See it here: {demourl}",
                "New release: {theme_name} - a fresh {category_text} WordPress theme for creating professional websites. Demo: {demourl}",
                "Just released: {theme_name} for {target_audience}. {selling_point}. See the demo: {demourl}"
            ]
        elif platform == "instagram":
            return [
                "🔥 NEW THEME ALERT 🔥\n\n{theme_name} - The ultimate WordPress solution for {category_text} websites\n\n#WordPressTheme #{category_hashtags} #WebDesign",
                "✨ Just Released: {theme_name} ✨\n\nOur newest {category_text} WordPress theme\n\n#WordPress #{category_hashtags} #WebDesign #NewRelease",
                "Introducing {theme_name} - our latest {category_text} WordPress theme!\n\nBuilt with {builder} for maximum flexibility\n\n#WordPress #WebDesign #{category_hashtags}",
                "✨ NEW: {theme_name} ✨\n\nA {theme_style} WordPress theme for {target_audience}\n\n{key_feature}\n\n#WordPress #{category_hashtags}"
            ]
        elif platform == "x":
            return [
                "🚀 Just launched: {theme_name} - our newest {category_text} WordPress theme! Built with {builder}. Check it out: {shortlink}",
                "Introducing {theme_name} v{version} - A brand new {category_text} WordPress theme now available! {shortlink}",
                "New release: {theme_name}, the perfect {category_text} WordPress theme for your next project. {shortlink}",
                "🆕 {theme_name}: A {theme_style} WordPress theme for {target_audience}. {selling_point} {shortlink}"
            ]
    else:
        # Templates for established themes
        if platform == "facebook":
            return [
                "Looking for a professional {category_text} WordPress theme? {theme_name} has everything you need. See it in action: {demourl}",
                "{theme_name} continues to be one of our most popular {category_text} WordPress themes. Find out why: {demourl}",
                "Create a stunning {category_text} website with our {theme_name} WordPress theme. Trusted by professionals worldwide. Preview: {demourl}",
                "{theme_name}: A {theme_style} WordPress theme perfect for {target_audience}. {key_feature}. See the demo: {demourl}"
            ]
        elif platform == "instagram":
            return [
                "Create stunning {category_text} websites with {theme_name} 💯\n\nPowered by {builder} for unlimited customization\n\n#WordPress #{category_hashtags} #WebDesign",
                "{theme_name}: Professional {category_text} WordPress theme ✨\n\nTrusted by creators worldwide\n\n#WordPress #WebDesign #{category_hashtags}",
                "Transform your {category_text} website with {theme_name} 🔥\n\nBuilt for professionals and beginners alike\n\n#WordPress #{category_hashtags} #WebDesign",
                "{theme_name}: A {theme_style} WordPress theme designed for {target_audience} ✨\n\n{key_feature}\n\n#WordPress #{category_hashtags}"
            ]
        elif platform == "x":
            return [
                "Create a professional {category_text} website with {theme_name}, our popular WordPress theme. Preview: {shortlink}",
                "{theme_name} v{version} - Trusted by {category_text} professionals worldwide. See what makes it special: {shortlink}",
                "Looking for a reliable {category_text} WordPress theme? {theme_name} has you covered with its powerful features. {shortlink}",
                "The {theme_style} design of {theme_name} makes it perfect for {target_audience}. {selling_point} {shortlink}"
            ]
    
    # Fall back to default templates if no specific ones match
    return all_templates if all_templates else [
        f"Check out {theme.get('name', '')}, our {format_category(theme.get('category', ''))} WordPress theme! {theme.get('demourl', '')}"
    ]

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
    
    # Format category properly
    category = theme.get("category", "")
    category_text = format_category(category)
    category_hashtags = format_hashtags(category)
    
    # Extract key features and target audience 
    key_feature = get_random_feature(theme.get("features", []))
    selling_point = get_random_feature(theme.get("selling_points", []))
    theme_style = format_list_to_text(theme.get("theme_style", []))
    target_audience = format_list_to_text(theme.get("target_audience", []))
    
    # Prepare context for template filling
    ctx = {
        "theme_name": theme.get("name", ""),
        "category": category,
        "category_text": category_text,
        "category_hashtags": category_hashtags,
        "builder": theme.get("builder", "WordPress"),
        "demourl": theme.get("demourl", ""),
        "shortlink": theme.get("shortlink", ""),
        "url": theme.get("url", ""),
        "version": theme.get("version", "1.0"),
        "updated": theme.get("updated", ""),
        "description": theme.get("description", ""),
        "key_feature": key_feature,
        "selling_point": selling_point,
        "theme_style": theme_style,
        "target_audience": target_audience
    }
    
    # Generate posts for each platform
    results = {}
    
    for platform in platforms:
        # Get templates appropriate for this theme and platform
        platform_templates = get_theme_templates(theme, platform, data)
        
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
                fallback = f"Check out {ctx['theme_name']}! {ctx['demourl']}"
                posts.append(fallback)
        
        results[platform] = posts
    
    return results
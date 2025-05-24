# agents/content/social_post_agent.py

import json
import random
import os
from datetime import datetime
import sys
from pathlib import Path

# Add the parent directory to sys.path to find utils
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]  # Go up to ai-crew directory
sys.path.append(str(project_root))

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

def get_enhanced_templates(theme, platform, data):
    """Enhanced template selection based on theme characteristics and available data"""
    
    # Get theme characteristics
    category = theme.get("category", "")
    target_audience = theme.get("target_audience", [])
    selling_points = theme.get("selling_points", [])
    testimonials = theme.get("testimonials", [])
    features = theme.get("features", [])
    theme_style = theme.get("theme_style", [])
    use_cases = theme.get("use_cases", [])
    
    # Check what rich content we have available
    has_testimonials = bool(testimonials)
    has_selling_points = bool(selling_points)
    has_rich_features = bool(features)
    has_use_cases = bool(use_cases)
    
    templates = []
    
    # TESTIMONIAL-BASED TEMPLATES (when available)
    if has_testimonials and platform in ["facebook", "instagram"]:
        top_testimonial = testimonials[0]  # Get the first testimonial
        if platform == "facebook":
            templates.extend([
                f'"{top_testimonial.get("text", "")}" - {top_testimonial.get("author", "")} ({top_testimonial.get("rating", 5)} stars)\n\nSee why {"{theme_name}"} is loved by users: {"{demourl}"}',
                f'⭐ {top_testimonial.get("rating", 5)}/5 Stars: "{top_testimonial.get("text", "")[:80]}..."\n\nDiscover {"{theme_name}"} - our {"{category_text}"} WordPress theme: {"{demourl}"}'
            ])
        elif platform == "instagram":
            templates.extend([
                f'⭐ {top_testimonial.get("rating", 5)}/5 STARS ⭐\n\n"{top_testimonial.get("text", "")[:100]}..."\n\n- {top_testimonial.get("author", "")}\n\n{"{theme_name}"} #{"{category_hashtags}"} #WordPress #CustomerLove',
                f'REAL USER REVIEW ✨\n\n"{top_testimonial.get("text", "")[:120]}..."\n\n{"{theme_name}"} - trusted by professionals\n\n#{"{category_hashtags}"} #WordPress #TestimonialTuesday'
            ])
    
    # FEATURE-FOCUSED TEMPLATES (when rich features available)
    if has_rich_features:
        key_features = features[:3]  # Get top 3 features
        if platform == "facebook":
            templates.extend([
                f'{"{theme_name}"} includes everything you need:\n\n✅ {key_features[0] if len(key_features) > 0 else "Professional design"}\n✅ {key_features[1] if len(key_features) > 1 else "Easy customization"}\n✅ {key_features[2] if len(key_features) > 2 else "Mobile responsive"}\n\nSee it in action: {"{demourl}"}',
                f'Why choose {"{theme_name}"}? Here are just 3 reasons:\n\n🔹 {key_features[0] if len(key_features) > 0 else "Professional design"}\n🔹 {key_features[1] if len(key_features) > 1 else "Easy customization"}\n🔹 {key_features[2] if len(key_features) > 2 else "Mobile responsive"}\n\nDiscover more: {"{demourl}"}'
            ])
        elif platform == "instagram":
            templates.extend([
                f'{"{theme_name}"} FEATURES 🔥\n\n✨ {key_features[0] if len(key_features) > 0 else "Professional design"}\n✨ {key_features[1] if len(key_features) > 1 else "Easy customization"}\n✨ {key_features[2] if len(key_features) > 2 else "Mobile responsive"}\n\n#{"{category_hashtags}"} #WordPress #WebDesign #Features',
                f'EVERYTHING YOU NEED ✅\n\n{key_features[0] if len(key_features) > 0 else "Professional design"} ✓\n{key_features[1] if len(key_features) > 1 else "Easy customization"} ✓\n{key_features[2] if len(key_features) > 2 else "Mobile responsive"} ✓\n\n{"{theme_name}"} has it all\n\n#{"{category_hashtags}"} #WordPress'
            ])
    
    # SELLING POINTS TEMPLATES (when available)
    if has_selling_points:
        top_selling_point = selling_points[0]
        if platform == "facebook":
            templates.extend([
                f'{"{theme_name}"}: {top_selling_point}\n\nPerfect for {"{target_audience}"} who want professional results without the complexity.\n\nDemo: {"{demourl}"}',
                f'Ready to {top_selling_point.lower()}?\n\n{"{theme_name}"} makes it possible with our {"{category_text}"} WordPress theme.\n\nSee how: {"{demourl}"}'
            ])
        elif platform == "instagram":
            templates.extend([
                f'{top_selling_point} ✨\n\nThat\'s the power of {"{theme_name}"}\n\n#{"{category_hashtags}"} #WordPress #WebDesign #Professional',
                f'GAME CHANGER 🚀\n\n{top_selling_point}\n\nWith {"{theme_name}"} it\'s possible\n\n#{"{category_hashtags}"} #WordPress #Success'
            ])
        elif platform == "x":
            templates.extend([
                f'{top_selling_point} That\'s what {"{theme_name}"} delivers. {"{shortlink}"}',
                f'Want to {top_selling_point.lower()}? {"{theme_name}"} makes it simple: {"{shortlink}"}'
            ])
    
    # USE CASE TEMPLATES (when available)
    if has_use_cases:
        primary_use_case = use_cases[0]
        if platform == "facebook":
            templates.append(f'Building a {primary_use_case.lower()}? {"{theme_name}"} is specifically designed for projects like yours.\n\n{"{selling_point}"}\n\nExplore the demo: {"{demourl}"}')
        elif platform == "instagram":
            templates.append(f'PERFECT FOR {primary_use_case.upper()} ✨\n\n{"{theme_name}"} - designed specifically for your needs\n\n#{"{category_hashtags}"} #WordPress #WebDesign')
        elif platform == "x":
            templates.append(f'{"{theme_name}"}: The go-to choice for {primary_use_case.lower()}. {"{shortlink}"}')
    
    # FALLBACK: Enhanced generic templates if no rich content
    if not templates:
        if platform == "facebook":
            templates = [
                f'Meet {"{theme_name}"} - our {"{category_text}"} WordPress theme designed for {"{target_audience}"}.\n\n{"{selling_point}"}\n\nSee it live: {"{demourl}"}',
                f'Looking for a {"{category_text}"} WordPress theme? {"{theme_name}"} offers {"{key_feature}"} and so much more.\n\nDemo: {"{demourl}"}'
            ]
        elif platform == "instagram":
            templates = [
                f'{"{theme_name}"} ✨\n\nYour new {"{category_text}"} WordPress theme\n\n{"{key_feature}"}\n\n#{"{category_hashtags}"} #WordPress #WebDesign',
                f'INTRODUCING {"{theme_name}"} 🔥\n\nBuilt for {"{target_audience}"}\n\n#{"{category_hashtags}"} #WordPress #WebDesign #NewTheme'
            ]
        elif platform == "x":
            templates = [
                f'{"{theme_name}"}: {"{selling_point}"} {"{shortlink}"}',
                f'New {"{category_text}"} WordPress theme: {"{theme_name}"}. {"{key_feature}"} {"{shortlink}"}'
            ]
    
    return templates

def get_theme_templates(theme, platform, data):
    """Get appropriate templates based on theme characteristics - ENHANCED VERSION"""
    
    # Use the enhanced template selection
    enhanced_templates = get_enhanced_templates(theme, platform, data)
    
    # If we got enhanced templates, return them
    if enhanced_templates:
        return enhanced_templates
    
    # Fallback to basic templates if enhanced fails
    all_templates = data["templates"].get("social_posts", {}).get(platform, [])
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
        # Get templates appropriate for this theme and platform (now uses enhanced logic)
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

# Test function for development
def test_enhanced_generation():
    """Test function to verify the enhanced template generation"""
    print("🧪 Testing Enhanced Social Post Generation\n")
    
    data = load_data()
    if not data["theme_data"]:
        print("❌ No theme data found")
        return
    
    # Test with a theme that has rich data (like 'decibel')
    test_theme_slug = "decibel"
    theme = data["theme_data"].get(test_theme_slug)
    
    if theme:
        print(f"📝 Testing with theme: {theme.get('name')}")
        print(f"   Has testimonials: {bool(theme.get('testimonials'))}")
        print(f"   Has selling points: {bool(theme.get('selling_points'))}")
        print(f"   Has features: {bool(theme.get('features'))}")
        
        # Generate actual posts
        posts = generate_posts(test_theme_slug, data=data, count=2)
        
        # Display results
        for platform, platform_posts in posts.items():
            print(f"\n{platform.upper()} posts:")
            for i, post in enumerate(platform_posts, 1):
                preview = post.replace('\n', ' ')[:120]
                print(f"{i}. {preview}...")
        
        print("\n✅ Enhanced generation test completed!")
    else:
        print(f"❌ Test theme '{test_theme_slug}' not found")

if __name__ == "__main__":
    test_enhanced_generation()

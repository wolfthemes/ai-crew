# agents/content/blog_writer_agent.py

import json
import random
import os

def load_data():
    """Load data required for blog post generation"""
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
        # Will be handled in the generation function
        pass
    
    # Load theme data
    try:
        with open('data/themes/theme_catalog.json', 'r') as f:
            data["theme_data"] = json.load(f)
    except FileNotFoundError:
        print("Theme catalog not found. Please ensure theme_catalog.json exists.")
    
    # Load categories
    try:
        with open('data/themes/theme_categories.json', 'r') as f:
            data["categories"] = json.load(f)
    except FileNotFoundError:
        # Will function without categories, just less specific
        pass
        
    return data

def generate_blog_post(theme_slug, post_type="review", data=None):
    """Generate a blog post for a theme
    
    Args:
        theme_slug (str): The theme's slug
        post_type (str): Type of post to generate (review, tutorial, showcase)
        data (dict): Optional pre-loaded data
        
    Returns:
        dict: Blog post content with title, content, and metadata
    """
    # Load data if not provided
    if data is None:
        data = load_data()
    
    # Get theme data
    theme = data["theme_data"].get(theme_slug)
    if not theme:
        return {"error": f"Theme '{theme_slug}' not found"}
    
    # Check for blog post templates
    templates = data["templates"].get("blog_posts", {})
    
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
    
    # Generate blog post title
    title_templates = [
        "{theme_name}: A Professional {category} WordPress Theme",
        "Introducing {theme_name} - The Ultimate {category} Theme",
        "Review: {theme_name} WordPress Theme for {category} Websites"
    ]
    title = random.choice(title_templates).format(**ctx)
    
    # Generate blog post content
    content_parts = []
    
    # Intro
    if "intro" in templates:
        intro = random.choice(templates["intro"]).format(**ctx)
    else:
        intro = f"Looking for the perfect {ctx['category']} WordPress theme? {ctx['theme_name']} might be exactly what you need."
    content_parts.append(intro)
    
    # Features section
    if "features" in templates:
        features = random.choice(templates["features"]).format(**ctx)
    else:
        features = f"## Key Features of {ctx['theme_name']}\n\n- Built with {ctx['builder']} for easy customization\n- Optimized for {ctx['category']} websites\n- Mobile-responsive design\n- Regular updates (last updated: {ctx['updated']})"
    content_parts.append("\n\n" + features)
    
    # Main content based on post type
    if post_type == "review":
        content_parts.append("\n\n## Why Choose " + ctx['theme_name'] + "?\n\n" +
            f"{ctx['theme_name']} stands out from other WordPress themes with its attention to detail and focus on {ctx['category']} functionality. " +
            f"Whether you're a professional {ctx['category']} website owner or just getting started, this theme provides all the tools you need to succeed online."
        )
    elif post_type == "tutorial":
        content_parts.append("\n\n## Getting Started with " + ctx['theme_name'] + "\n\n" +
            f"Setting up {ctx['theme_name']} is straightforward. After purchasing and installing the theme, you'll have access to a comprehensive dashboard " +
            f"where you can customize every aspect of your {ctx['category']} website. Let's walk through the basic setup process."
        )
    else:  # showcase
        content_parts.append("\n\n## {theme_name} in Action\n\n" +
            f"To give you a better idea of what {ctx['theme_name']} can do, let's look at some examples of the theme in use. " +
            f"These real-world implementations showcase the versatility and professional quality of {ctx['theme_name']}."
        )
    
    # CTA
    if "cta" in templates:
        cta = random.choice(templates["cta"]).format(**ctx)
    else:
        cta = f"Ready to take your {ctx['category']} website to the next level? [Check out {ctx['theme_name']} today]({ctx['url']})."
    content_parts.append("\n\n" + cta)
    
    # Combine all parts
    content = "".join(content_parts)
    
    return {
        "title": title,
        "content": content,
        "metadata": {
            "theme": theme_slug,
            "post_type": post_type,
            "category": ctx["category"],
            "tags": [theme_slug, ctx["category"], ctx["builder"], "wordpress theme"]
        }
    }
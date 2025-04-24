# crews/content_crew.py (updated)

import json
import os
from agents.content import social_post_agent, buffer_integration_agent

def generate_social_campaign(theme_slug, platforms=None, post_count=1):
    """Generate a social media campaign for a specific theme"""
    # Load shared data once
    data = social_post_agent.load_data()
    
    # Generate posts using the shared data
    posts = social_post_agent.generate_posts(
        theme_slug, 
        platforms=platforms, 
        count=post_count,
        data=data
    )
    
    return posts

def schedule_to_buffer(posts, schedule_times=None):
    """Schedule posts to Buffer
    
    Args:
        posts (dict): Posts to schedule by platform
        schedule_times (dict): Optional scheduling times
        
    Returns:
        dict: Scheduling results
    """
    return buffer_integration_agent.schedule_posts(posts, schedule=schedule_times)

def run_theme_promotion(theme_slug, platforms=None, post_count=1, schedule=True):
    """Run a complete theme promotion workflow"""
    # Generate the posts
    posts = generate_social_campaign(theme_slug, platforms, post_count)
    
    results = {
        "theme": theme_slug,
        "generated_posts": posts
    }
    
    # Schedule if requested
    if schedule:
        scheduling_results = schedule_to_buffer(posts)
        results["scheduling"] = scheduling_results
    
    return results
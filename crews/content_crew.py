# crews/content_crew.py

import json
import os
from agents.content import social_post_agent

def generate_social_campaign(theme_slug, platforms=None, post_count=1):
    """Generate a social media campaign for a specific theme
    
    Args:
        theme_slug (str): The theme's slug
        platforms (list): Platforms to generate content for
        post_count (int): Number of posts per platform
        
    Returns:
        dict: Generated posts by platform
    """
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
    """Schedule posts to Buffer (placeholder for now)
    
    Args:
        posts (dict): Posts to schedule by platform
        schedule_times (dict): Optional scheduling times
        
    Returns:
        dict: Scheduling results
    """
    # This would be implemented later with Buffer API integration
    return {
        "status": "simulated",
        "message": "Posts would be scheduled to Buffer (not implemented yet)",
        "post_count": sum(len(platform_posts) for platform_posts in posts.values())
    }
# agents/content/buffer_integration_agent.py

import requests
import json
import os
from datetime import datetime, timedelta

# Buffer API endpoints
BUFFER_API_BASE = "https://api.bufferapp.com/1/"
PROFILES_ENDPOINT = BUFFER_API_BASE + "profiles.json"
UPDATES_ENDPOINT = BUFFER_API_BASE + "updates/create.json"

def get_buffer_token():
    """Get Buffer API token from environment or config file"""
    # First check environment variable
    token = os.environ.get("BUFFER_ACCESS_TOKEN")
    
    # If not in environment, try config file
    if not token:
        try:
            with open('data/config/buffer_config.json', 'r') as f:
                config = json.load(f)
                token = config.get("access_token")
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    return token

def get_profiles(token=None):
    """Get Buffer connected social profiles"""
    if token is None:
        token = get_buffer_token()
        
    if not token:
        return {"error": "No Buffer access token found"}
    
    try:
        response = requests.get(
            PROFILES_ENDPOINT,
            params={"access_token": token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Buffer API error: {response.status_code}", "details": response.text}
            
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def create_posting_schedule(profiles, start_time=None, days=7, posts_per_day=1):
    """Create a posting schedule across different profiles
    
    Args:
        profiles (list): Buffer profile objects
        start_time (datetime): When to start posting (defaults to tomorrow)
        days (int): Number of days to schedule
        posts_per_day (int): Posts per day per profile
        
    Returns:
        dict: Schedule by profile ID and platform
    """
    if start_time is None:
        # Default to tomorrow at 10am
        start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        start_time += timedelta(days=1)
    
    schedule = {}
    
    for profile in profiles:
        profile_id = profile.get("id")
        service = profile.get("service")  # facebook, twitter, instagram, etc.
        
        if not profile_id or not service:
            continue
            
        # Create schedule for this profile
        profile_schedule = []
        
        for day in range(days):
            for post_num in range(posts_per_day):
                # Add some variation to posting times
                post_time = start_time + timedelta(
                    days=day,
                    hours=post_num * 2 + (service == "instagram" and 1 or 0)  # Stagger by platform
                )
                
                profile_schedule.append(post_time.isoformat())
        
        schedule[profile_id] = {
            "service": service,
            "times": profile_schedule
        }
    
    return schedule

def schedule_posts(posts, schedule=None, token=None):
    """Schedule posts to Buffer
    
    Args:
        posts (dict): Posts by platform (facebook, instagram, x/twitter)
        schedule (dict): Optional predetermined schedule
        token (str): Buffer API token
        
    Returns:
        dict: Results of scheduling
    """
    if token is None:
        token = get_buffer_token()
        
    if not token:
        return {"error": "No Buffer access token found"}
    
    # Get profiles if no schedule provided
    if schedule is None:
        profiles_response = get_profiles(token)
        
        if "error" in profiles_response:
            return profiles_response
            
        profiles = profiles_response
        schedule = create_posting_schedule(profiles)
    
    results = {
        "scheduled": [],
        "failed": []
    }
    
    # Map our platform names to Buffer's service names
    platform_to_service = {
        "facebook": "facebook",
        "instagram": "instagram",
        "x": "twitter"
    }
    
    # Schedule each post
    for platform, platform_posts in posts.items():
        service = platform_to_service.get(platform)
        if not service:
            results["failed"].append({
                "platform": platform,
                "error": f"Unknown platform mapping: {platform}"
            })
            continue
        
        # Find matching profiles for this service
        matching_profiles = {}
        for profile_id, profile_data in schedule.items():
            if profile_data.get("service") == service:
                matching_profiles[profile_id] = profile_data
        
        if not matching_profiles:
            results["failed"].append({
                "platform": platform,
                "error": f"No Buffer profiles found for service: {service}"
            })
            continue
        
        # Schedule posts for each matching profile
        for profile_id, profile_data in matching_profiles.items():
            times = profile_data.get("times", [])
            
            for i, post in enumerate(platform_posts):
                if i >= len(times):
                    # No more times available in schedule
                    break
                
                # Schedule this post
                try:
                    response = requests.post(
                        UPDATES_ENDPOINT,
                        params={
                            "access_token": token,
                            "profile_id": profile_id,
                            "text": post,
                            "scheduled_at": times[i]
                        }
                    )
                    
                    if response.status_code == 200:
                        results["scheduled"].append({
                            "platform": platform,
                            "profile_id": profile_id,
                            "post": post,
                            "scheduled_at": times[i]
                        })
                    else:
                        results["failed"].append({
                            "platform": platform,
                            "profile_id": profile_id,
                            "post": post,
                            "error": f"Buffer API error: {response.status_code}",
                            "details": response.text
                        })
                        
                except Exception as e:
                    results["failed"].append({
                        "platform": platform,
                        "profile_id": profile_id,
                        "post": post,
                        "error": f"Request failed: {str(e)}"
                    })
    
    return results
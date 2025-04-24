# test_content_crew.py
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from crews import content_crew

def main():
    # Test generating social posts
    theme_slug = "decibel"  # From your theme_catalog.json
    posts = content_crew.generate_social_campaign(theme_slug, post_count=2)
    
    print(f"Generated posts for {theme_slug}:")
    for platform, platform_posts in posts.items():
        print(f"\n{platform.upper()}:")
        for post in platform_posts:
            print(f"  - {post}")
    
    # Test scheduling (simulation)
    result = content_crew.schedule_to_buffer(posts)
    print(f"\nScheduling result: {result}")

if __name__ == "__main__":
    main()
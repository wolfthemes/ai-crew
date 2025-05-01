# test_content_crew.py
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# test_improved_posts.py

from agents.content import social_post_agent

def main():
    # Load data once
    data = social_post_agent.load_data()
    
    # Test with a newer theme
    new_theme = "poize"  # One of your newer themes
    print(f"\n=== Generated posts for {new_theme} (newer theme) ===")
    posts = social_post_agent.generate_posts(new_theme, count=2, data=data)
    
    for platform, platform_posts in posts.items():
        print(f"\n{platform.upper()}:")
        for post in platform_posts:
            print(f"  - {post}")
    
    # Test with an established theme
    established_theme = "mediafoundry"  # One of your older themes
    print(f"\n\n=== Generated posts for {established_theme} (established theme) ===")
    posts = social_post_agent.generate_posts(established_theme, count=2, data=data)
    
    for platform, platform_posts in posts.items():
        print(f"\n{platform.upper()}:")
        for post in platform_posts:
            print(f"  - {post}")

if __name__ == "__main__":
    main()
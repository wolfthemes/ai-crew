import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import argparse
from datetime import datetime

async def extract_theme_data(url):
    """Extract theme metadata from ThemeForest page with enhanced music theme detection"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        print(f"Navigating to {url}")
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        # Get theme name
        theme_name = await page.text_content('h1.t-heading.-size-l')
        theme_name = theme_name.strip() if theme_name else "Unknown Theme"
        print(f"Extracting data for: {theme_name}")
        
        # Get main description
        description = await page.text_content('.item-description')
        
        # Check if this is a music-related theme
        music_keywords = [
            "music", "band", "artist", "audio", "record", "sound", 
            "concert", "festival", "dj", "producer", "album", "track",
            "musician", "singer", "songwriter", "playlist", "label", "recording studio"
        ]
        is_music_theme = any(keyword in description.lower() or keyword in theme_name.lower() 
                             for keyword in music_keywords)
        
        if is_music_theme:
            print("Detected a music-related theme!")
        
        # Extract features
        feature_elements = await page.query_selector_all('.feature-list li, .item-description ul li')
        features = []
        for el in feature_elements:
            feature_text = await el.text_content()
            # Clean up and filter relevant features
            if len(feature_text.strip()) > 3 and not feature_text.startswith('http'):
                features.append(feature_text.strip())
        
        # Remove duplicates and limit to top features
        features = list(set(features))[:15]
        print(f"Found {len(features)} features")
        
        # Extract theme category/type from breadcrumbs
        category_element = await page.query_selector('.breadcrumb a:nth-child(2)')
        category = await category_element.text_content() if category_element else "WordPress"
        
        # Look for certain keywords to determine theme style
        theme_style = []
        style_keywords = {
            "Modern": ["modern", "contemporary", "fresh"],
            "Clean": ["clean", "minimal", "simple", "elegant"],
            "Bold": ["bold", "dynamic", "vibrant"],
            "Creative": ["creative", "unique", "artistic"],
            "Professional": ["professional", "business", "corporate"]
        }
        
        for style, keywords in style_keywords.items():
            if any(keyword in description.lower() for keyword in keywords):
                theme_style.append(style)
        
        # Try to determine target audience
        audience_matches = re.findall(r'perfect for ([^.]+)', description.lower())
        target_audience = []
        for match in audience_matches:
            audience_segments = [segment.strip().title() for segment in match.split(',')]
            target_audience.extend(audience_segments)
        
        # If it's a music theme, add music-specific audiences
        if is_music_theme and not target_audience:
            if "band" in description.lower() or "band" in theme_name.lower():
                target_audience.extend(["Bands", "Musicians", "Music Artists"])
            elif "dj" in description.lower() or "dj" in theme_name.lower():
                target_audience.extend(["DJs", "Electronic Music Artists", "Producers"])
            elif "festival" in description.lower() or "festival" in theme_name.lower():
                target_audience.extend(["Music Festival Organizers", "Event Managers", "Concert Venues"])
            elif "label" in description.lower() or "record" in description.lower():
                target_audience.extend(["Record Labels", "Music Production Companies", "Audio Studios"])
            elif "recording" in description.lower() or "record" in description.lower():
                target_audience.extend(["Recording Studio", "Music Production", "Sound Engineer"])
            else:
                target_audience.extend(["Musicians", "Bands", "Music Industry Professionals"])
        
        # Extract compatible plugins
        compatible_plugins = []
        plugin_patterns = ["elementor", "woocommerce", "wpbakery", "revslider", "contact form", "loco translate", "variation-swatches-for-woocommerce", "yoast"]
        
        # Add music-specific plugins
        wolf_plugins = ["wolf-events", "wolf-albums", "wolf-discography", "wolf-jobs", "wolf-portfolio", "wolf-photos", "wolf-popup", 
                         "wolf-artists", "wolf-playlist-manager", "wolf-videos", "wolf-woocommerce-wishlist"]
        
        all_plugins = plugin_patterns + wolf_plugins
        
        for pattern in all_plugins:
            if pattern in description.lower():
                if pattern.startswith("wolf"):
                    plugin_name = pattern.title().replace("Wolf ", "Wolf ")
                else:
                    plugin_name = pattern.title() if pattern != "wpml" else "WPML"
                    plugin_name = "Contact Form 7" if pattern == "contact form" else plugin_name
                    plugin_name = "Events" if pattern == "wolf-events" else plugin_name
                    plugin_name = "WooCommerce Wishlist" if pattern == "wolf-woocommerce-wishlist" else plugin_name
                compatible_plugins.append(plugin_name)
        
        # Generate selling points
        selling_points = []
        selling_point_patterns = [
            r'(?:feature|highlight|include)[ds]?\s+([^.]+)',
            r'(?:perfect|ideal|great)\s+for\s+([^.]+)',
            r'(?:fully|completely)\s+([^.]+)'
        ]
        
        for pattern in selling_point_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:  # Only meaningful phrases
                    selling_points.append(match.strip().capitalize())
        
        # If it's a music theme, look for music-specific selling points
        if is_music_theme:
            music_selling_point_patterns = [
                r'(?:music|audio|band|artist)[^.]*(?:feature|showcase|display)[^.]*',
                r'(?:album|track|event)[^.]*(?:manage|display|showcase)[^.]*',
                r'(?:concert|tour|gig)[^.]*(?:list|display|promote)[^.]*'
            ]
            
            for pattern in music_selling_point_patterns:
                matches = re.findall(pattern, description, re.IGNORECASE)
                for match in matches:
                    if len(match) > 10:
                        selling_points.append(match.strip().capitalize())
        
        # Limit to top selling points
        selling_points = list(set(selling_points))[:7]
        
        # Try to identify design features
        design_features = []
        design_patterns = [
            "responsive", "retina", "dark mode", "light mode", 
            "animation", "parallax", "video background", "slider", "masonry"
        ]
        
        # Add music-specific design features
        if is_music_theme:
            music_design_patterns = [
                "audio player", "music player", "playlist", 
                "album artwork", "discography layout", "event calendar"
            ]
            design_patterns.extend(music_design_patterns)
        
        for pattern in design_patterns:
            if pattern in description.lower():
                feature_name = pattern.title() + (" Support" if pattern in ["responsive", "retina"] else "")
                design_features.append(feature_name)
        
        # Generate use cases based on theme type and features
        use_cases = []
        
        # General use cases
        if "portfolio" in " ".join(features).lower():
            use_cases.append(f"{category} Portfolio Websites")
        
        if "shop" in " ".join(features).lower() or "woocommerce" in " ".join(compatible_plugins).lower():
            use_cases.append(f"{category} Online Stores")
        
        # Music-specific use cases
        if is_music_theme:
            # Look for specific music theme types
            if "band" in description.lower() or "band" in theme_name.lower():
                use_cases.append("Band & Musician Websites")
            
            if "dj" in description.lower() or "dj" in theme_name.lower():
                use_cases.append("DJ & Producer Websites")
            
            if "festival" in description.lower() or "event" in description.lower():
                use_cases.append("Music Festival & Event Websites")
            
            if "label" in description.lower() or "record" in description.lower():
                use_cases.append("Record Label Websites")
            
            if "podcast" in description.lower() or "radio" in description.lower():
                use_cases.append("Podcast & Radio Websites")
            
            if "studio" in description.lower():
                use_cases.append("Recording Studio Websites")
            
            # Add generic music use case if none of the specifics matched
            if not any(x in " ".join(use_cases).lower() for x in ["band", "dj", "festival", "label", "podcast", "studio"]):
                use_cases.append("Music Industry Websites")
        else:
            # Add default use case if none detected
            if not use_cases:
                use_cases.append(f"{category} Business Websites")
        
        # Extract testimonials
        testimonials = []
        try:
            # First check if reviews tab exists
            reviews_tab = await page.query_selector('a[href="#item-reviews"]')
            if reviews_tab:
                await reviews_tab.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_selector('.review-list', timeout=5000)
                
                # Get review elements
                review_elements = await page.query_selector_all('.review-list .review-item')
                
                for review_el in review_elements[:5]:  # Limit to top 5 reviews
                    # Get review text
                    comment_el = await review_el.query_selector('.review-body .comment-content')
                    if not comment_el:
                        comment_el = await review_el.query_selector('.review-body')
                    
                    comment = await comment_el.text_content() if comment_el else ""
                    
                    # Get author
                    author_el = await review_el.query_selector('.reviewer-name')
                    author = await author_el.text_content() if author_el else "Customer"
                    
                    if comment:
                        # Format testimonial
                        testimonial = f"{comment.strip()} - {author.strip()}"
                        testimonials.append(testimonial)
                
                print(f"Found {len(testimonials)} testimonials")
        except Exception as e:
            print(f"Error extracting testimonials: {e}")
        
        # Generate key benefits
        key_benefits = []
        
        # For music themes, create music-specific benefits
        if is_music_theme:
            if "band" in description.lower() or "artist" in description.lower():
                key_benefits.append("Showcase your music with integrated audio players")
                key_benefits.append("Display upcoming tour dates and concert information")
                key_benefits.append("Sell merchandise directly through your website")
            
            if "event" in description.lower() or "festival" in description.lower():
                key_benefits.append("Highlight festival lineups and event schedules")
                key_benefits.append("Sell tickets directly through your website")
                key_benefits.append("Showcase past events with photo galleries")
            
            if "label" in description.lower() or "producer" in description.lower():
                key_benefits.append("Promote your artist roster effectively")
                key_benefits.append("Showcase your discography and releases")
                key_benefits.append("Integrate with music streaming platforms")
        
        # If no music-specific benefits were added, use the selling points
        if not key_benefits:
            key_benefits = selling_points[:5] if len(selling_points) > 5 else selling_points
        
        await browser.close()
        
        # Format the output
        output = {
            "features": features,
            "selling_points": selling_points,
            "theme_style": theme_style,
            "target_audience": target_audience,
            "key_benefits": key_benefits,
            "compatible_plugins": compatible_plugins,
            "design_features": design_features,
            "use_cases": use_cases,
            "testimonials": testimonials,
            "is_music_theme": is_music_theme
        }
        
        return theme_name, output

async def main():
    parser = argparse.ArgumentParser(description='Scrape ThemeForest page for theme metadata with music theme enhancements')
    parser.add_argument('url', help='ThemeForest theme URL')
    parser.add_argument('--output', '-o', help='Output file path', default='')
    
    args = parser.parse_args()
    
    theme_name, data = await extract_theme_data(args.url)
    
    # Generate output filename if not provided
    if not args.output:
        theme_slug = theme_name.lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/themes/scraped/{theme_slug}_scraped_{timestamp}.json"
    else:
        output_file = args.output
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Scraped data saved to {output_file}")
    if data["is_music_theme"]:
        print("✓ Music theme detected and enhanced music-specific content generated")

if __name__ == "__main__":
    asyncio.run(main())
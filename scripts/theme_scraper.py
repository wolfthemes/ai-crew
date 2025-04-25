import asyncio
import json
import os
import re
from playwright.async_api import async_playwright
import argparse
from datetime import datetime

def clean_text(text):
    """Clean extracted text for better quality"""
    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove HTML/XML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Fix common formatting issues
    text = text.replace('  –', ' – ')
    text = text.replace('  -', ' - ')
    text = text.replace('(109 value)', '($109 value)')
    
    return text

def is_valid_content(text, min_length=10, max_length=200):
    """Check if content is valid and useful"""
    # Check length
    if len(text) < min_length or len(text) > max_length:
        return False
    
    # Check for common page elements that aren't useful
    unwanted_patterns = [
        r'follow us on', r'subscribe to', r'newsletter', r'stay tuned', 
        r'view more', r'explore the', r'click here', r'check out our',
        r'join our', r'read more about', r'learn more about', r'get started with',
        r'copyright', r'all rights reserved'
    ]
    
    if any(re.search(pattern, text.lower()) for pattern in unwanted_patterns):
        return False
    
    return True

def classify_content(text):
    """Determine if text is a feature or selling point"""
    # Feature indicators - technical specifications, included items
    feature_indicators = [
        "included", "integration", "plugin", "built with", "templates",
        "responsive", "customization", "optimized", "compatible with",
        "support for", "comes with", "pre-built", "ready for"
    ]
    
    # Selling point indicators - benefits, outcomes, value
    selling_point_indicators = [
        "helps you", "allows you", "enables you to", "perfect for",
        "attract", "increase", "improve", "boost", "create", "showcase",
        "sell your", "connect with", "stand out", "impress your"
    ]
    
    text_lower = text.lower()
    
    # Check for feature indicators
    feature_score = sum(2 for indicator in feature_indicators if indicator in text_lower)
    
    # Check for selling point indicators
    selling_point_score = sum(2 for indicator in selling_point_indicators if indicator in text_lower)
    
    # Add points for structural indicators
    if any(text_lower.startswith(prefix) for prefix in ["included", "support for", "integration with", "built with"]):
        feature_score += 3
    
    if any(text_lower.startswith(prefix) for prefix in ["create", "build", "showcase", "attract", "perfect for"]):
        selling_point_score += 3
    
    # Technical specifications are features
    if re.search(r'\d+\s*(GB|MB|items|templates|pages|layouts)', text_lower):
        feature_score += 3
    
    # If it's much more likely to be one or the other, return that
    if feature_score > selling_point_score + 2:
        return "feature"
    if selling_point_score > feature_score + 2:
        return "selling_point"
    
    # Default case - if short, likely a feature; if longer, likely a selling point
    return "feature" if len(text) < 60 else "selling_point"

async def extract_theme_data(url):
    """Extract theme metadata from ThemeForest page with enhanced content classification"""
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
            "musician", "singer", "songwriter", "playlist", "label", "studio"
        ]
        is_music_theme = any(keyword in description.lower() or keyword in theme_name.lower() 
                             for keyword in music_keywords)
        
        if is_music_theme:
            print("Detected a music-related theme!")
        
        # Extract content items from various sources
        content_items = []
        
        # Try feature list items
        feature_elements = await page.query_selector_all('.feature-list li')
        for el in feature_elements:
            feature_text = await el.text_content()
            feature_text = clean_text(feature_text)
            if is_valid_content(feature_text):
                content_items.append(feature_text)
        
        # Try bullet lists in the description
        list_elements = await page.query_selector_all('.item-description ul li')
        for el in list_elements:
            item_text = await el.text_content()
            item_text = clean_text(item_text)
            if is_valid_content(item_text) and item_text not in content_items:
                content_items.append(item_text)
        
        # Extract headings which might indicate features - FIXED APPROACH
        heading_elements = await page.query_selector_all('.item-description h1, .item-description h2, .item-description h3')
        for el in heading_elements:
            heading_text = await el.text_content()
            if "feature" in heading_text.lower() or "include" in heading_text.lower():
                # Instead of evaluating JS, use a safer approach to get text from next elements
                try:
                    # Use a more direct JS evaluation to get paragraph text
                    next_paragraph = await page.evaluate('''
                    (heading) => {
                        let paragraphs = [];
                        let current = heading.nextElementSibling;
                        while (current && ['P', 'UL', 'OL'].indexOf(current.tagName) === -1 && paragraphs.length < 3) {
                            current = current.nextElementSibling;
                        }
                        
                        if (current && current.textContent) {
                            return current.textContent.trim();
                        }
                        return null;
                    }
                    ''', el)
                    
                    if next_paragraph:
                        paragraph_text = clean_text(next_paragraph)
                        if is_valid_content(paragraph_text, min_length=20):
                            content_items.append(paragraph_text)
                except Exception as e:
                    print(f"Error getting paragraph after heading: {e}")
        
        # Look for sentences with feature-like patterns
        feature_sentences = re.findall(r'[A-Z][^.!?]*(?:feature|include|come with|built with|support)[^.!?]*[.!?]', description)
        for sentence in feature_sentences:
            sentence_text = clean_text(sentence)
            if is_valid_content(sentence_text) and sentence_text not in content_items:
                content_items.append(sentence_text)
        
        # Classify content items into features and selling points
        features = []
        selling_points = []
        
        for item in content_items:
            category = classify_content(item)
            if category == "feature" and item not in features:
                features.append(item)
            elif category == "selling_point" and item not in selling_points:
                selling_points.append(item)
        
        # Ensure we have enough features
        if len(features) < 5:
            # Add basic features based on description analysis
            potential_features = [
                "Fully responsive design",
                "SEO optimized structure",
                "Regular theme updates",
                "Comprehensive documentation"
            ]
            
            if "elementor" in description.lower():
                potential_features.append("Built with Elementor page builder")
            
            if "woocommerce" in description.lower():
                potential_features.append("WooCommerce compatible")
            
            if "revolution" in description.lower() or "slider revolution" in description.lower():
                potential_features.append("Slider Revolution plugin included")
            
            # Add missing features
            for feature in potential_features:
                if feature not in features:
                    features.append(feature)
                    if len(features) >= 7:
                        break
        
        # Ensure we have enough selling points
        if len(selling_points) < 5:
            # Generate selling points based on theme type
            if is_music_theme:
                music_selling_points = []
                
                if "studio" in theme_name.lower() or "studio" in description.lower():
                    music_selling_points = [
                        "Create a professional recording studio website that attracts clients",
                        "Showcase your studio services with industry-specific layouts",
                        "Display your equipment and facilities with stunning visuals",
                        "Generate more bookings with integrated contact forms",
                        "Present your portfolio of productions to build credibility"
                    ]
                elif "band" in theme_name.lower() or "artist" in description.lower():
                    music_selling_points = [
                        "Build a professional website for your band or music project",
                        "Showcase your music with integrated audio players",
                        "Promote upcoming shows and tours effectively",
                        "Sell merchandise directly to your fans",
                        "Connect with your audience through social media integration"
                    ]
                elif "festival" in theme_name.lower() or "event" in description.lower():
                    music_selling_points = [
                        "Create an engaging festival or music event website",
                        "Showcase your lineup with artist profiles",
                        "Display event schedules and venue information",
                        "Sell tickets directly through your website",
                        "Build excitement with countdown timers and announcements"
                    ]
                else:
                    music_selling_points = [
                        "Create a professional music industry website",
                        "Showcase your work with audio and video integration",
                        "Connect with your audience through engaging layouts",
                        "Sell your music and merchandise online",
                        "Stand out with industry-specific design elements"
                    ]
                
                # Add missing selling points
                for point in music_selling_points:
                    if point not in selling_points:
                        selling_points.append(point)
                        if len(selling_points) >= 5:
                            break
            else:
                # Generic selling points
                generic_selling_points = [
                    f"Create a professional {theme_name} website with minimal setup time",
                    "Attract more visitors with a modern, eye-catching design",
                    "Save time with pre-built pages and layouts",
                    "Increase conversions with optimized user experience",
                    "Stand out from competitors with unique design elements"
                ]
                
                # Add missing selling points
                for point in generic_selling_points:
                    if point not in selling_points:
                        selling_points.append(point)
                        if len(selling_points) >= 5:
                            break
        
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
        target_audience = []
        audience_patterns = [
            r'perfect for ([^.]+)',
            r'designed for ([^.]+)',
            r'ideal for ([^.]+)',
            r'made for ([^.]+)',
            r'targeted at ([^.]+)',
            r'created for ([^.]+)'
        ]
        
        for pattern in audience_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                segments = re.split(r',|\sand\s', match)
                for segment in segments:
                    segment = segment.strip().title()
                    if len(segment) > 3 and segment not in target_audience:
                        target_audience.append(segment)
        
        # If it's a music theme, add music-specific audiences
        if is_music_theme and not target_audience:
            if "band" in description.lower() or "band" in theme_name.lower():
                target_audience.extend(["Bands", "Musicians", "Music Artists"])
            elif "dj" in description.lower() or "dj" in theme_name.lower():
                target_audience.extend(["DJs", "Electronic Music Artists", "Producers"])
            elif "festival" in description.lower() or "festival" in theme_name.lower():
                target_audience.extend(["Music Festival Organizers", "Event Managers", "Concert Venues"])
            elif "label" in description.lower() or "record" in description.lower():
                target_audience.extend(["Record Labels", "Music Production Companies"])
            elif "studio" in description.lower():
                target_audience.extend(["Recording Studios", "Audio Engineers", "Music Producers"])
            else:
                target_audience.extend(["Musicians", "Bands", "Music Industry Professionals"])
        
        # Extract compatible plugins
        compatible_plugins = []
        plugin_patterns = [
            "elementor", "woocommerce", "wpbakery", "contact form 7", "wpml", 
            "yoast seo", "jetpack", "slider revolution", "visual composer"
        ]
        
        # Add music-specific plugins
        music_plugins = [
            "wolf music", "wolf events", "wolf albums", "wolf discography", 
            "wolf bands", "wolf artists", "wolf audio", "wolf videos"
        ]
        
        all_plugins = plugin_patterns + music_plugins
        
        for pattern in all_plugins:
            if pattern in description.lower():
                if pattern.startswith("wolf"):
                    plugin_name = pattern.title().replace("Wolf ", "Wolf ")
                else:
                    plugin_name = pattern.title() if pattern != "wpml" else "WPML"
                    plugin_name = "Contact Form 7" if pattern == "contact form 7" else plugin_name
                    plugin_name = "Slider Revolution" if pattern == "slider revolution" else plugin_name
                compatible_plugins.append(plugin_name)
        
        # Try to identify design features
        design_features = []
        design_patterns = [
            "responsive", "retina", "dark mode", "light mode", 
            "animation", "parallax", "video background", "slider",
            "drag and drop", "flexible layout", "grid system"
        ]
        
        # Add music-specific design features
        if is_music_theme:
            music_design_patterns = [
                "audio player", "music player", "playlist", "waveform", 
                "album artwork", "discography layout", "event calendar"
            ]
            design_patterns.extend(music_design_patterns)
        
        for pattern in design_patterns:
            if pattern in description.lower():
                feature_name = pattern.title()
                if pattern in ["responsive", "retina"]:
                    feature_name += " Support"
                design_features.append(feature_name)
        
        # Generate use cases based on theme type and features
        use_cases = []
        
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
            
            if "studio" in description.lower() or "studio" in theme_name.lower():
                use_cases.append("Recording Studio Websites")
            
            # Add generic music use case if none of the specifics matched
            if not any(x in " ".join(use_cases).lower() for x in ["band", "dj", "festival", "label", "podcast", "studio"]):
                use_cases.append("Music Industry Websites")
        
        # General use cases
        if "portfolio" in " ".join(features).lower() or "portfolio" in description.lower():
            use_cases.append(f"{category} Portfolio Websites")
        
        if "shop" in " ".join(features).lower() or "woocommerce" in " ".join(compatible_plugins).lower():
            use_cases.append(f"{category} Online Stores")
        
        # Add default use case if none detected
        if not use_cases:
            use_cases.append(f"{category} Business Websites")
        
        # For testimonials, just create a placeholder - user will handle this manually
        testimonials = []
        
        # Generate key benefits - music-specific or based on selling points
        key_benefits = []
        
        # For music themes, create music-specific benefits
        if is_music_theme:
            if "band" in description.lower() or "artist" in description.lower():
                key_benefits = [
                    "Showcase your music with integrated audio players",
                    "Display upcoming tour dates and concert information",
                    "Sell merchandise directly through your website",
                    "Connect with fans through social media integration",
                    "Present your discography in an appealing layout"
                ]
            elif "event" in description.lower() or "festival" in description.lower():
                key_benefits = [
                    "Highlight festival lineups and event schedules",
                    "Sell tickets directly through your website",
                    "Showcase past events with photo galleries",
                    "Interactive maps for venue locations",
                    "Countdown timers for upcoming events"
                ]
            elif "label" in description.lower() or "producer" in description.lower():
                key_benefits = [
                    "Promote your artist roster effectively",
                    "Showcase your discography and releases",
                    "Integrate with music streaming platforms",
                    "Present new releases with feature highlights",
                    "Sell music and merchandise directly to fans"
                ]
            elif "studio" in description.lower() or "studio" in theme_name.lower():
                key_benefits = [
                    "Showcase your studio facilities and equipment",
                    "Display your production portfolio with audio samples",
                    "Online booking system for studio sessions",
                    "Client testimonials and success stories",
                    "Pricing tables for different service packages"
                ]
        
        # If no key benefits defined yet, use selling points
        if not key_benefits and selling_points:
            key_benefits = selling_points[:5]
        
        # If still not enough benefits, add generic ones
        if len(key_benefits) < 3:
            generic_benefits = [
                f"Professional {category} website with minimal setup time",
                "Mobile-optimized design for all devices",
                "SEO-friendly structure for better search visibility",
                "Regular updates and dedicated support",
                "Easy customization without coding knowledge"
            ]
            
            # Add missing benefits
            needed = 5 - len(key_benefits)
            key_benefits.extend(generic_benefits[:needed])
        
        await browser.close()
        
        # Format the output - ensure we have high-quality, ready-to-use data
        output = {
            "features": features[:10],  # Limit to top 10
            "selling_points": selling_points[:7],  # Limit to top 7
            "theme_style": theme_style[:3] if theme_style else ["Modern", "Professional"],  # Default if none found
            "target_audience": target_audience[:5],  # Limit to top 5
            "key_benefits": key_benefits[:5],  # Limit to top 5
            "compatible_plugins": compatible_plugins[:7],  # Limit to top 7
            "design_features": design_features[:7],  # Limit to top 7
            "use_cases": use_cases[:5],  # Limit to top 5
            "testimonials": [],  # Empty array - user will handle manually
            "customer_sites": [],  # Empty array for customer sites
            "category": category,  # The category extracted from breadcrumbs
            "is_music_theme": is_music_theme
        }
        
        return theme_name, output

async def main():
    
    parser = argparse.ArgumentParser(description='Scrape ThemeForest page for theme metadata with enhanced content classification')
    parser.add_argument('url', nargs='?', help='ThemeForest theme URL')
    parser.add_argument('--output', '-o',help='Output file path', default='')
    parser.add_argument('--batch', '-b',  action='store_true', help='Process all themes in theme catalog')
    
    args = parser.parse_args()
    
    if args.batch:
        print("Batch theme meta")
        catalog_path = os.path.abspath('data/themes/theme_catalog.json')
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
            print(f"Loaded theme catalog with {len(catalog)} themes")

            for theme_slug, theme_data in catalog.items():
                if 'url' not in theme_data:
                    print(f"Skipping {theme_slug}: No URL found")
                    continue
                url = theme_data['url']
                print(f"\n{'='*50}")
                print(f"Processing {theme_slug}: {url}")
                output_dir  ="data/themes/scraped"
                output_file = os.path.join(output_dir, f"theme_meta_{theme_slug}.json")
                empty, data = await extract_theme_data(url)
                print(f"Processing {theme_slug}")
                #return
                
                # Save to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        return
    else:
    
        theme_name, data = await extract_theme_data(args.url)

        # Generate output filename if not provided
        if not args.output:
            theme_slug = theme_name.lower().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = rf"C:\Users\const\Local Sites\wolf-core-supertheme\app\public\wp-content\themes\wolf-supertheme\THEMES/unimate/theme_meta.json"
            base_dir = r"C:\Users\const\Local Sites\wolf-core-supertheme\app\public\wp-content\themes\wolf-supertheme\THEMES"
            output_file = os.path.join(base_dir, "unimate", "theme_meta.json")
        else:
            output_file = args.output
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Scraped data saved to {output_file}")
        
        # Print summary
        print("\nExtraction Summary:")
        print(f"- Features: {len(data['features'])}")
        print(f"- Selling Points: {len(data['selling_points'])}")
        print(f"- Use Cases: {len(data['use_cases'])}")
        print(f"- Compatible Plugins: {len(data['compatible_plugins'])}")
        
        if data["is_music_theme"]:
            print("✓ Music theme detected and music-specific content generated")

if __name__ == "__main__":
    asyncio.run(main())
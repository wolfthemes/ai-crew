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
    
    # Remove special characters
    text = re.sub(r'[^\w\s.,!?&\-\'":;()]', '', text)
    
    return text

def is_valid_content(text, min_length=15, max_length=150):
    """Check if content is valid and useful"""
    # Check length (not too short, not too long)
    if len(text) < min_length or len(text) > max_length:
        return False
    
    # Check if it's a complete phrase (generally starts with capital letter)
    if not text[0].isupper() and not text[0].isdigit():
        return False
    
    # Check for common page elements that aren't useful
    unwanted_patterns = [
        r'follow us', r'subscribe', r'newsletter', r'stay tuned', 
        r'view', r'explore', r'click', r'check', r'download',
        r'join', r'read more', r'learn more', r'get started'
    ]
    
    if any(re.search(pattern, text.lower()) for pattern in unwanted_patterns):
        return False
    
    # Ensure it's not just a heading or label
    if len(text.split()) < 4:
        return False
    
    return True

def extract_meaningful_phrases(text, prefix_patterns=None):
    """Extract complete, meaningful phrases from text"""
    if prefix_patterns is None:
        prefix_patterns = [
            r'Features?', r'Includes?', r'Offers?', r'Provides?', 
            r'Supports?', r'Enables?', r'Allows?', r'Helps?'
        ]
    
    # Split by common sentence delimiters
    sentences = re.split(r'[.!?]\s+', text)
    
    # Clean each sentence
    sentences = [clean_text(s) for s in sentences if s.strip()]
    
    # Filter for valid content
    valid_sentences = [s for s in sentences if is_valid_content(s)]
    
    # Look for phrases that match the patterns
    pattern_matches = []
    for pattern in prefix_patterns:
        for sentence in valid_sentences:
            matches = re.finditer(r'(' + pattern + r'\s+[^.!?]+)', sentence, re.IGNORECASE)
            for match in matches:
                phrase = match.group(0)
                if is_valid_content(phrase):
                    pattern_matches.append(phrase)
    
    # Combine both direct sentences and pattern matches, removing duplicates
    all_phrases = list(set(valid_sentences + pattern_matches))
    
    return all_phrases

async def extract_theme_data(url):
    """Extract theme metadata from ThemeForest page with enhanced content filtering"""
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
        
        # Extract features - use a more targeted approach
        features = []
        
        # First try to get feature list items
        feature_elements = await page.query_selector_all('.feature-list li')
        for el in feature_elements:
            feature_text = await el.text_content()
            feature_text = clean_text(feature_text)
            if is_valid_content(feature_text, min_length=10):
                features.append(feature_text)
        
        # If no specific feature list found, extract from description
        if not features:
            # Look for bullet lists in the description
            list_elements = await page.query_selector_all('.item-description ul li')
            for el in list_elements:
                feature_text = await el.text_content()
                feature_text = clean_text(feature_text)
                if is_valid_content(feature_text, min_length=10):
                    features.append(feature_text)
        
        # If still no features, extract from the description text
        if not features:
            # Look for feature-like sentences
            feature_phrases = extract_meaningful_phrases(description, [
                r'Features?', r'Includes?', r'Offers?', r'Provides?', 
                r'Supports?', r'Built with', r'Integrated with'
            ])
            features.extend(feature_phrases)
        
        # Limit features and remove duplicates
        features = list(set(features))[:12]  # limit to reasonable number
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
        
        # Generate selling points - using a more targeted approach
        selling_points = []
        
        # Direct selling point extraction
        selling_point_patterns = [
            r'(?:feature|highlight|include)[ds]?\s+([^.!?]+[.!?])',
            r'(?:perfect|ideal|great)\s+for\s+([^.!?]+[.!?])',
            r'(?:fully|completely)\s+([^.!?]+[.!?])'
        ]
        
        for pattern in selling_point_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                point = clean_text(match)
                if is_valid_content(point):
                    selling_points.append(point)
        
        # If no selling points found, create them from features
        if not selling_points and features:
            for feature in features[:5]:  # Use top 5 features
                if is_valid_content(feature):
                    selling_points.append(feature)
        
        # Music-specific selling points
        if is_music_theme and len(selling_points) < 5:
            music_selling_points = [
                "Perfect for showcasing your music and connecting with fans",
                "Integrated audio players to feature your tracks and releases",
                "Specialized layouts for music events and performances",
                "Designed specifically for music industry professionals",
                "Showcase your musical portfolio with style and elegance"
            ]
            
            if "studio" in theme_name.lower() or "studio" in description.lower():
                music_selling_points = [
                    "Showcase your studio's capabilities and equipment",
                    "Highlight your production work and client testimonials",
                    "Present your services and rates in a professional manner",
                    "Integrated audio players to demonstrate sound quality",
                    "Booking system for studio time and sessions"
                ]
            
            # Add missing selling points up to 5
            needed = 5 - len(selling_points)
            if needed > 0:
                selling_points.extend(music_selling_points[:needed])
        
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
        
        # Generate key benefits - these should be high quality
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
        
        # If no key benefits defined yet, extract from features
        if not key_benefits:
            # Use the best features as benefits
            top_features = sorted(features, key=len)[-5:] if features else []
            for feature in top_features:
                if is_valid_content(feature):
                    key_benefits.append(feature)
        
        # If still not enough benefits, add generic ones based on category
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
            "theme_style": theme_style[:3],  # Limit to top 3
            "target_audience": target_audience[:5],  # Limit to top 5
            "key_benefits": key_benefits[:5],  # Limit to top 5
            "compatible_plugins": compatible_plugins[:7],  # Limit to top 7
            "design_features": design_features[:7],  # Limit to top 7
            "use_cases": use_cases[:5],  # Limit to top 5
            "is_music_theme": is_music_theme
        }
        
        return theme_name, output
    
async def extract_testimonials(url):
    """Extract testimonials from ThemeForest review page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=True in production
        page = await browser.new_page()
        
        print(f"Navigating to {url}")
        
        # Navigate directly to the reviews page
        if not url.endswith('/reviews'):
            if '/reviews/' in url:
                # URL is already correct
                pass
            else:
                url = url.replace('/item/', '/item/reviews/')
        
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        # Wait a bit for dynamic content
        await asyncio.sleep(2)
        
        testimonials = []
        try:
            # Check if any reviews are loaded
            review_count = await page.evaluate('''
                document.querySelectorAll('.user-review').length
            ''')
            
            print(f"Found {review_count} reviews with primary selector")
            
            if review_count > 0:
                # Extract with the newer review structure
                reviews_data = await page.evaluate('''
                    Array.from(document.querySelectorAll('.user-review')).slice(0, 5).map(review => {
                        const ratingEl = review.querySelector('.rating-text');
                        const rating = ratingEl ? parseInt(ratingEl.textContent.trim().split('/')[0]) : 0;
                        
                        const commentEl = review.querySelector('.review__comment');
                        const comment = commentEl ? commentEl.textContent.trim() : "";
                        
                        const authorEl = review.querySelector('.review__name');
                        const author = authorEl ? authorEl.textContent.trim() : "Customer";
                        
                        return {rating, comment, author};
                    })
                ''')
                
                for review in reviews_data:
                    if review['rating'] >= 4 and review['comment']:
                        testimonial = f"{review['comment']} - {review['author']}"
                        testimonials.append(testimonial)
            else:
                # Try alternative selector structure
                review_count = await page.evaluate('''
                    document.querySelectorAll('.review-list .review-item').length
                ''')
                
                print(f"Found {review_count} reviews with alternative selector")
                
                if review_count > 0:
                    # Extract with the older review structure
                    reviews_data = await page.evaluate('''
                        Array.from(document.querySelectorAll('.review-list .review-item')).slice(0, 5).map(review => {
                            const ratingEl = review.querySelector('.rating');
                            const rating = ratingEl ? parseInt(ratingEl.getAttribute('data-rating')) : 0;
                            
                            const commentEl = review.querySelector('.review-body .comment-content');
                            const comment = commentEl ? commentEl.textContent.trim() : "";
                            
                            const authorEl = review.querySelector('.reviewer-name');
                            const author = authorEl ? authorEl.textContent.trim() : "Customer";
                            
                            return {rating, comment, author};
                        })
                    ''')
                    
                    for review in reviews_data:
                        if review['rating'] >= 4 and review['comment']:
                            testimonial = f"{review['comment']} - {review['author']}"
                            testimonials.append(testimonial)
                else:
                    # Try a third structure that sometimes appears
                    review_count = await page.evaluate('''
                        document.querySelectorAll('.js-reviews .js-review').length
                    ''')
                    
                    print(f"Found {review_count} reviews with third selector")
                    
                    if review_count > 0:
                        # Extract with another review structure
                        reviews_data = await page.evaluate('''
                            Array.from(document.querySelectorAll('.js-reviews .js-review')).slice(0, 5).map(review => {
                                const ratingStars = review.querySelectorAll('.js-stars-filter');
                                const rating = ratingStars.length;
                                
                                const commentEl = review.querySelector('.js-review-body');
                                const comment = commentEl ? commentEl.textContent.trim() : "";
                                
                                const authorEl = review.querySelector('.js-reviewer-name');
                                const author = authorEl ? authorEl.textContent.trim() : "Customer";
                                
                                return {rating, comment, author};
                            })
                        ''')
                        
                        for review in reviews_data:
                            if review['rating'] >= 4 and review['comment']:
                                testimonial = f"{review['comment']} - {review['author']}"
                                testimonials.append(testimonial)
            
            print(f"Successfully extracted {len(testimonials)} testimonials")
            
            # Take screenshots for debugging
            await page.screenshot(path="review_page.png")
            
        except Exception as e:
            print(f"Error extracting testimonials: {e}")
        
        await browser.close()
        return testimonials

async def main():
    parser = argparse.ArgumentParser(description='Scrape ThemeForest page for theme metadata with enhanced content filtering')
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

    # testimonials = await extract_testimonials("https://themeforest.net/item/gainlab-music-recording-studio-wordpress-theme/reviews/48383694")
    
    # print("\nExtracted Testimonials:")
    # for i, testimonial in enumerate(testimonials, 1):
    #     print(f"{i}. {testimonial}")
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Scraped data saved to {output_file}")
    if data["is_music_theme"]:
        print("✓ Music theme detected and enhanced music-specific content generated")

if __name__ == "__main__":
    asyncio.run(main())
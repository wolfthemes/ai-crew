import re
import json
import os
from typing import Dict, Optional, List

class EnhancedTicketParser:
    def __init__(self, ticket_text: str):
        self.ticket_text = ticket_text
        self.theme_catalog = self._load_theme_catalog()
        self.theme_names = self._build_theme_name_list()

    def _load_theme_catalog(self) -> Dict:
        """Load the theme catalog from JSON file"""
        try:
            catalog_path = os.path.join("data", "themes", "theme_catalog.json")
            with open(catalog_path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load theme catalog: {e}")
            return {}

    def _build_theme_name_list(self) -> List[tuple]:
        """Build a list of (theme_name, theme_slug) tuples for matching"""
        theme_list = []
        for slug, theme_data in self.theme_catalog.items():
            theme_name = theme_data.get("name", "")
            if theme_name:
                theme_list.append((theme_name.lower(), slug))
                theme_list.append((slug.lower(), slug))  # Also match by slug
        return theme_list

    def extract_theme_name(self) -> Optional[str]:
        """Extract theme name from ticket text by matching against catalog"""
        text_lower = self.ticket_text.lower()
        
        # Look for theme names in the text
        for theme_name, theme_slug in self.theme_names:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(theme_name) + r'\b'
            if re.search(pattern, text_lower):
                return theme_slug
        
        return None

    def get_theme_data(self, theme_slug: str) -> Dict:
        """Get theme data from catalog by slug"""
        return self.theme_catalog.get(theme_slug, {})

    def extract_customer_urls(self) -> List[str]:
        """Extract URLs that are likely customer sites (not WolfThemes or Envato)"""
        # Find all URLs in the text
        url_pattern = r'https?://[^\s<>"\'\)\]\}]+'
        urls = re.findall(url_pattern, self.ticket_text, re.IGNORECASE)
        
        # Filter out our own URLs and Envato URLs
        excluded_domains = [
            'wolfthemes',
            'envato',
            'themeforest',
            'preview.wolfthemes',
            'wlfthm.es'
        ]
        
        customer_urls = []
        for url in urls:
            is_excluded = False
            for domain in excluded_domains:
                if domain in url.lower():
                    is_excluded = True
                    break
            if not is_excluded:
                customer_urls.append(url)
        
        return customer_urls

    def extract_customer_name(self) -> str:
        """Simple customer name extraction (fallback method)"""
        lines = self.ticket_text.strip().splitlines()
        candidates = [l.strip() for l in lines if 1 <= len(l.strip().split()) <= 3]
        return candidates[-1] if candidates else "Customer"

    def get_ticket_metadata(self) -> Dict:
        """
        Extract ticket metadata similar to get_ticket_metadata() function
        Returns the same structure for compatibility
        """
        # Extract theme information
        theme_slug = self.extract_theme_name()
        theme_data = self.get_theme_data(theme_slug) if theme_slug else {}
        
        # Extract URLs
        customer_urls = self.extract_customer_urls()
        user_site = customer_urls[0] if customer_urls else "—"
        
        # Extract customer name
        customer_name = self.extract_customer_name()
        
        # Build metadata structure matching get_ticket_metadata format
        metadata = {
            "ticket_id": None,  # No ticket ID for fresh tickets
            "timestamp": None,
            "ticket_type": "email",  # Assuming fresh tickets are emails
            "subject": "Fresh Ticket",
            "customer": customer_name,
            "customer_url": None,
            "theme": theme_data.get("name", "Unknown"),
            "builder": theme_data.get("builder", "Unknown"),
            "included_plugins": theme_data.get("included_plugins", "Not Provided"),
            "category": theme_data.get("category", ["Uncategorized"]),
            "version": theme_data.get("version", "No version found"),
            "theme_url": theme_data.get("url", "Unknown"),
            "theme_demo_url": theme_data.get("demourl", "Unknown"),
            "envato_id": theme_data.get("itemId", "Unknown"),
            "updated": theme_data.get("updated", "No date available"),
            "user_site": user_site,
            "ticket_url": None,
            "first_message": self.ticket_text,
            "last_message": self.ticket_text,
            "last_message_timestamp": None,
            "last_message_summary": "Fresh ticket",
            "full_thread_summary": "Fresh ticket submission",
            "formatted_text_thread": self.ticket_text,
            "contains_credentials": self._contains_credentials(),
            "match_source": "fresh_ticket",
            "ai_reply": "",
            "full_thread": [],
            "flags": {
                "needs_human": False,
                "private": False
            }
        }
        
        return metadata

    def _contains_credentials(self) -> bool:
        """Detect if the text includes login credentials"""
        patterns = [
            r"wp-admin", r"username[:\s]", r"password[:\s]",
            r"login[:\s]", r"ftp", r"site access", r"admin login"
        ]
        text = self.ticket_text.lower()
        return any(re.search(p, text) for p in patterns)

    # Legacy methods for backward compatibility
    def extract_url(self):
        """Legacy method - returns first customer URL or None"""
        urls = self.extract_customer_urls()
        return urls[0] if urls else None

    def extract_theme_slug(self):
        """Legacy method - returns theme slug"""
        return self.extract_theme_name() or "Unknown"

    def split_into_parts(self):
        """Legacy method - split text into parts"""
        return [p.strip() for p in re.split(r"\n|[?]", self.ticket_text) if len(p.strip()) > 10]

    def extract_all(self):
        """Legacy method - returns old format for backward compatibility"""
        theme_slug = self.extract_theme_name()
        theme_data = self.get_theme_data(theme_slug) if theme_slug else {}
        
        return {
            "customer_name": self.extract_customer_name(),
            "theme": theme_data.get("name", "Unknown"),
            "url": self.extract_url(),
            "parts": self.split_into_parts()
        }


# Convenience function to maintain compatibility with existing code
def parse_fresh_ticket_metadata(ticket_text: str) -> Dict:
    """
    Parse ticket text and return metadata in the same format as get_ticket_metadata()
    
    Args:
        ticket_text (str): Raw ticket text to parse
        
    Returns:
        dict: Ticket metadata in the same format as get_ticket_metadata()
    """
    parser = EnhancedTicketParser(ticket_text)
    return parser.get_ticket_metadata()


# Example usage:
if __name__ == "__main__":
    # Test with sample ticket text
    sample_text = """
    Hi,
    
    I'm having trouble with my Decibel theme. The music player is not working on my site https://myband.com.
    I've checked the settings but can't figure it out.
    
    Thanks,
    John Smith
    """
    
    parser = EnhancedTicketParser(sample_text)
    metadata = parser.get_ticket_metadata()
    
    print("Extracted metadata:")
    print(f"Theme: {metadata['theme']}")
    print(f"Customer: {metadata['customer']}")
    print(f"User Site: {metadata['user_site']}")
    print(f"Builder: {metadata['builder']}")
    print(f"Theme URL: {metadata['theme_url']}")
    print( metadata )

import re

class TicketParser:
    def __init__(self, ticket_text: str):
        self.ticket_text = ticket_text

    def extract_customer_name(self):
        # Simple: look for a line with a name at the end
        lines = self.ticket_text.strip().splitlines()
        candidates = [l.strip() for l in lines if 1 <= len(l.strip().split()) <= 3]
        return candidates[-1] if candidates else "Customer"

    def extract_theme_slug(self):
        # Dummy value for now
        return "herion"

    def extract_url(self):
        urls = re.findall(r'https?://[^\s]+', self.ticket_text)
        return urls[0] if urls else None

    def split_into_parts(self):
        # Naive: split by line or ?
        return [p.strip() for p in re.split(r"\n|[?]", self.ticket_text) if len(p.strip()) > 10]

    def extract_all(self):
        return {
            "customer_name": self.extract_customer_name(),
            "theme": self.extract_theme_slug(),
            "url": self.extract_url(),
            "parts": self.split_into_parts()
        }

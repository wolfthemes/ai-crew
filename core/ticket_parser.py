import re

class TicketParser:
    def __init__(self, ticket_text: str):
        self.ticket_text = ticket_text

    def extract_customer_name(self):
        lines = self.ticket_text.splitlines()
        possible_names = [l.strip() for l in lines if len(l.strip().split()) <= 2 and len(l.strip()) > 1]
        return possible_names[-1] if possible_names else "Customer"

    def extract_theme_slug(self):
        # Placeholder: You might infer from ticket or metadata
        return "herion"

    def extract_url(self):
        matches = re.findall(r'https?://[^\s]+', self.ticket_text)
        return matches[0] if matches else None

    def split_into_parts(self):
        # Naive: split by question marks, new lines, etc.
        return [p.strip() for p in re.split(r"\n|[?]", self.ticket_text) if p.strip()]

    def extract_all(self):
        return {
            "customer_name": self.extract_customer_name(),
            "theme": self.extract_theme_slug(),
            "url": self.extract_url(),
            "parts": self.split_into_parts()
        }

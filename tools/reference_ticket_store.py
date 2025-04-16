# tools/reference_ticket_store.py

import re
import json

class ReferenceTicketStore:
    def __init__(self, path="data/static/reference_tickets.json"):
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def find_match(self, text):
        for ref in self.data:
            pattern = ref.get("pattern", "")
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "source": ref.get("source"),
                    "title": ref.get("title"),
                    "content": f"STRICT_RESPONSE: {ref.get('strict_response')}",
                    "is_strict": True
                }
        return None

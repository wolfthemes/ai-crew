# tools/common_issue_store.py

import re
import json

class CommonIssueStore:
    def __init__(self, path="data/static/common_issues.json"):
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def find_match(self, text):
        for issue in self.data:
            pattern = issue.get("pattern", "")
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "source": "common_issue",
                    "title": issue.get("title"),
                    "content": f"STRICT_RESPONSE: {issue.get('strict_response')}",
                    "is_strict": True
                }
        return None

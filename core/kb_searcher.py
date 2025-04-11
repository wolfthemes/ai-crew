class KnowledgeBaseSearcher:
    def __init__(self, theme: str, resources: dict):
        """
        `resources` should include:
          - common_issues
          - kb_articles
          - theme_note
          - theme_doc
          - support_ticket
        """
        self.theme = theme
        self.resources = resources

    def find_best_match(self, issue_summary: str) -> dict:
        """
        Searches for the issue in the resources using strict priority.

        Returns:
        {
            "matched_source": "common_issues",
            "content_used": "Here is the solution...",
        }
        """
        # TODO: implement strict-priority lookup
        return {}

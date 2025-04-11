class TicketParser:
    def __init__(self, ticket_data: dict):
        self.ticket_data = ticket_data

    def extract_issues(self) -> list[dict]:
        """
        Splits the ticket text into one or more distinct problems.

        Returns a list of dicts like:
        [
            {
                "issue_summary": "The demo import fails at 70%",
                "full_text": "...",  # optional raw section
                "related_theme": "Omnity",
                "client_url": "https://example.com"  # if available
            }
        ]
        """
        # TODO: implement parsing logic
        return []

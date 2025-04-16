from core.reranker import rerank_results
from tools.reference_ticket_store import ReferenceTicketStore

class KnowledgeBaseSearcher:
    def __init__(self, retriever, context: dict):
        self.context = context
        self.retriever = retriever
        self.reference_store = ReferenceTicketStore()

    def find_best_match(self, query: str) -> dict:
        """Structured search with layered priority: common > reference > kb > doc"""

        if not self.retriever:
            return {
                "error": "Retriever not loaded",
                "matches": {},
                "strict_response": None
            }

        matches = {
            "common_issue": None,
            "reference_ticket": None,
            "kb": [],
            "theme_doc": [],
            "old_ticket": [],
        }
        strict_response = None

        # 🔍 1. Search and rerank all results
        results = rerank_results(self.retriever.invoke(query))

        if not results:
            return {
                "matches": matches,
                "strict_response": None
            }

        # 🔎 2. Check for common issue
        for doc in results:
            if doc.metadata.get("issue_type") == "common_issue":
                matches["common_issue"] = {
                    "source": "common_issue",
                    "title": doc.metadata.get("title", "Common Issue"),
                    "content": f"STRICT_RESPONSE: {doc.metadata.get('expected_response')}",
                    "is_strict": True
                }
                strict_response = matches["common_issue"]["content"]
                return {
                    "matches": matches,
                    "strict_response": strict_response
                }

        # 📎 3. Check for reference ticket match
        ref_match = self.reference_store.find_match(query, theme=self.context.get("theme"))
        if ref_match:
            matches["reference_ticket"] = ref_match
            strict_response = ref_match["content"]
            return {
                "matches": matches,
                "strict_response": strict_response
            }

        # 📚 4. Add non-strict results to KB and Theme Doc groups
        for doc in results:
            category = doc.metadata.get("source", "")
            match_data = {
                "title": doc.metadata.get("title", "Untitled"),
                "url": doc.metadata.get("url", ""),
                "snippet": doc.page_content[:500]
            }

            if category == "kb_article":
                matches["kb"].append(match_data)
            elif category == "theme_doc":
                matches["theme_doc"].append(match_data)

        return {
            "matches": matches,
            "strict_response": None
        }

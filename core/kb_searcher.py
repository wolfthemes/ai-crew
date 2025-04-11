from core.reranker import rerank_results

class KnowledgeBaseSearcher:
    def __init__(self, theme: str, retriever):
        self.theme = theme
        self.retriever = retriever

    def find_best_match(self, query: str) -> dict:
        """Structured search using strict priority and reranking logic."""

        if not self.retriever:
            return {
                "source": "error",
                "title": "Retrieval Error",
                "content": "Retrieval is disabled. Vectorstore not loaded."
            }

        results = rerank_results(self.retriever.invoke(query))

        if not results:
            return {
                "source": "none",
                "title": "No Results",
                "content": "No relevant results found in the knowledge base."
            }

        # Return structured data for common issues with a special prefix
        common_issues = [doc for doc in results if doc.metadata.get("issue_type") == "common_issue"]
        if common_issues:
            return {
                "source": "common_issue",
                "title": common_issues[0].metadata.get("title", "Common Issue"),
                "content": f"STRICT_RESPONSE: {common_issues[0].metadata.get('expected_response')}",
                "is_strict": True
            }

        # # Fallback: general best match
        # first_result = results[0]
        # return {
        #     "source": first_result.metadata.get("source", "unknown"),
        #     "title": first_result.metadata.get("title", "Untitled"),
        #     "url": first_result.metadata.get("url", ""),
        #     "content": first_result.page_content[:1000],
        #     "is_strict": False,
        #     "all_results": [
        #         {
        #             "source": doc.metadata.get("source", "unknown"),
        #             "title": doc.metadata.get("title", "Untitled"),
        #             "url": doc.metadata.get("url", ""),
        #             "snippet": doc.page_content[:300]
        #         }
        #         for doc in results[1:3]
        #     ]
        # }

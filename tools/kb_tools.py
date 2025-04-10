from langchain_core.documents import Document
from crewai.tools import tool
import os
import json

def rerank_results(results):
    """Sort results by priority type"""
    priority_map = {
        "common_issue": 1,
        "kb_article": 2,
        "theme_note": 3,
        "theme_doc": 4,
        "support_ticket": 5
    }
    return sorted(results, key=lambda doc: priority_map.get(doc.metadata.get("source", ""), 99))

def search_kb_raw(query: str, retriever=None):
    """Raw search function that returns structured data from the KB"""
    if not retriever:
        return {
            "source": "error",
            "title": "Retrieval Error",
            "content": "Retrieval is disabled. Vectorstore not loaded."
        }

    results = rerank_results(retriever.invoke(query))

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

    # Fallback: return first result in structured format
    first_result = results[0]
    return {
        "source": first_result.metadata.get("source", "unknown"),
        "title": first_result.metadata.get("title", "Untitled"),
        "url": first_result.metadata.get("url", ""),
        "content": first_result.page_content[:1000],
        "is_strict": False,
        "all_results": [
            {
                "source": doc.metadata.get("source", "unknown"),
                "title": doc.metadata.get("title", "Untitled"),
                "url": doc.metadata.get("url", ""),
                "snippet": doc.page_content[:300]
            }
            for doc in results[1:3]  # Include 2 additional results
        ]
    }
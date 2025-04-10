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
    """
    Search the common issues, WolfThemes documentation, KB articles, and past tickets for the given query string.
    If a common issue is found, return ONLY the expected_response field as a STRICT_RESPONSE that must be used verbatim.
    """

    if not retriever:
        return "Retrieval is disabled. Vectorstore not loaded."

    results = rerank_results(retriever.invoke(query))

    if not results:
        return "No relevant results found in the knowledge base."

    # Return ONLY expected_response for common issues with a special prefix
    common_issues = [doc for doc in results if doc.metadata.get("issue_type") == "common_issue"]
    if common_issues:
        return f"STRICT_RESPONSE: {common_issues[0].metadata.get('expected_response')}"

    # Fallback: return first few general results
    return "\n\n".join([
        f"📄 {doc.metadata.get('title')} ({doc.metadata.get('source', '')})"
        f"\n🔗 {doc.metadata.get('url', '')}"
        f"\n{doc.page_content[:300]}..."
        for doc in results[:3]
    ]) or "No relevant results found."
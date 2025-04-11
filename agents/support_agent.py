
import os
import json
from crewai import Agent
from tools.vector_retriever import support_agent_backstory_text

# def search_kb_structured(query: str):
#     """Raw search function that returns structured string data from the KB"""
#     if not retriever:
#         return {
#             "source": "error",
#             "title": "Retrieval Error",
#             "content": "Retrieval is disabled. Vectorstore not loaded."
#         }

#     results = rerank_results(retriever.invoke(query))

#     if not results:
#         return {
#             "source": "none",
#             "title": "No Results",
#             "content": "No relevant results found in the knowledge base."
#         }

#     # Return structured data for common issues with a special prefix
#     common_issues = [doc for doc in results if doc.metadata.get("issue_type") == "common_issue"]
#     if common_issues:
#         return {
#             "source": "common_issue",
#             "title": common_issues[0].metadata.get("title", "Common Issue"),
#             "content": f"STRICT_RESPONSE: {common_issues[0].metadata.get('expected_response')}",
#             "is_strict": True
#         }



# @tool("SearchKnowledgeBase")
# def search_kb(query: str):
#     """
#     Search the common issues, WolfThemes documentation, KB articles, and past tickets for the given query string.
#     If a common issue is found, return ONLY the expected_response field as a STRICT_RESPONSE that must be used verbatim.
#     """

#     if not retriever:
#         return "Retrieval is disabled. Vectorstore not loaded."

#     results = rerank_results(retriever.invoke(query))

#     if not results:
#         return "No relevant results found in the knowledge base."

#     # Return ONLY expected_response for common issues with a special prefix
#     common_issues = [doc for doc in results if doc.metadata.get("issue_type") == "common_issue"]
#     if common_issues:
#         return f"STRICT_RESPONSE: {common_issues[0].metadata.get('expected_response')}"

#     # Fallback: return first few general results
#     return "\n\n".join([
#         f"📄 {doc.metadata.get('title')} ({doc.metadata.get('source', '')})"
#         f"\n🔗 {doc.metadata.get('url', '')}"
#         f"\n{doc.page_content[:300]}..."
#         for doc in results[:3]
#     ]) or "No relevant results found."

### Agent
support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory = support_agent_backstory_text,
    tools=[],
    allow_delegation=False,
    verbose=True,
    instructions="""
1. You are given a ticket and a structured summary of the research done.
2. If a part includes a STRICT_RESPONSE, you must include it exactly in your reply.
3. If no STRICT_RESPONSE is found, you may generate a helpful reply based on the KB matches.
4. Always add a greeting and sign-off.
5. Format the final message in Markdown.
"""
)

if __name__ == "__main__":
    print(f"✅ Agent initialized.")


import os
import json
import time

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from crewai import Agent
from crewai.tools import tool

from tools.vector_retriever import retriever, agent_backstory_text

start = time.time()
load_dotenv()


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

### Tools

@tool("GetThemeBuilder")
def get_theme_builder(slug: str):
    """Return the page builder used by a given theme slug."""
    try:
        with open(os.path.join(retriever.DATA_FOLDER, "theme_info.json"), encoding="utf-8") as f:
            data = json.load(f)
        theme = data.get(slug)
        if theme:
            return f"{theme['name']} uses {theme['builder']}."
        else:
            return f"No info found for theme '{slug}'."
    except Exception as e:
        return f"Error retrieving theme info: {e}"
    

@tool("SearchKnowledgeBase")
def search_kb(query: str):
    """
    Search all available KB sources and return the most relevant result.
    If a STRICT_RESPONSE is found in common issues, it will be returned directly.
    """
    from tools.kb_tools import search_kb_structured

    result = search_kb_structured(query, retriever)

    print(f"🛠️ TOOL CALLED with query: {query}")
    print(f"🔁 Tool result:\n{result}")

    if not result:
        return "No results found in the KB."

    if result.get("is_strict"):
        return result["content"]

    return "\n\n".join([
        f"📄 {result['title']} ({result['source']})"
        f"\n🔗 {result.get('url', '')}"
        f"\n{result['content'][:300]}..."
    ] + [
        f"\n\n🔎 Additional: {r['title']} ({r['source']})\n{r['snippet'][:200]}..."
        for r in result.get("all_results", [])
    ])

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
    backstory = agent_backstory_text,
    tools=[search_kb, get_theme_builder],
    allow_delegation=False,
    verbose=True,
    instructions="""
Your job is to answer a customer support ticket.

You MUST follow these steps precisely:
1. Call the `SearchKnowledgeBase` tool using the ticket text.
2. Check if the response begins with "STRICT_RESPONSE:". If it does:
   - Extract the text after "STRICT_RESPONSE:" and use it VERBATIM in your reply
   - Do not modify, elaborate, or add to this response in any way
3. If the response does not begin with "STRICT_RESPONSE:", you may formulate a helpful response based on the retrieved information.
4. Always add a greeting at the beginning and a professional closing at the end.

Format your reply as:
Hi there,

{RESPONSE CONTENT}

I hope this helps!

Best regards,
Support Team
"""
)

if __name__ == "__main__":
    print(f"✅ Agent initialized in {time.time() - start:.2f} seconds.")

import os
import json
from crewai import Agent
from crewai.tools import tool
from tools.vector_retriever import retriever

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

research_agent = Agent(
    role="Support Research Assistant",
    goal="Extract all issues from a support ticket and find structured KB solutions",
    backstory=(
        "You're a detail-oriented assistant who helps the support agent "
        "by splitting tickets into clear issues, identifying the theme and builder, "
        "and finding existing solutions from the KB if available."
    ),
    tools=[search_kb,get_theme_builder],
    verbose=True,
)

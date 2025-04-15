from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from tools.kb_tools import search_kb_structured
from tools.vector_retriever import retriever
import os
import json

# --- Tool: SearchKnowledgeBase ---

class SearchKBInput(BaseModel):
    query: str = Field(..., description="The query to search in the knowledge base")

class SearchKnowledgeBaseTool(BaseTool):
    name: str = "SearchKnowledgeBase"
    description: str = "Searches all KB sources and returns a result or STRICT_RESPONSE if matched."
    args_schema: Type[BaseModel] = SearchKBInput

    def _run(self, query: str) -> str:
        result = search_kb_structured(query, retriever)

        if not result:
            return "No results found."

        if result.get("is_strict"):
            return f"STRICT_RESPONSE: {result['content']}"

        return "\n\n".join([
            f"📄 {result['title']} ({result['source']})"
            f"\n🔗 {result.get('url', '')}"
            f"\n{result['content'][:300]}..."
        ] + [
            f"\n\n🔎 Additional: {r['title']} ({r['source']})\n{r['snippet'][:200]}..."
            for r in result.get("all_results", [])
        ])
    
    def run(self, query: str) -> str:
        return self._run(query)


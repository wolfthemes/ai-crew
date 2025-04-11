from tools.kb_tools import search_kb_structured
from tools.vector_retriever import retriever

query = "how to update wpbakery in herion"

result = search_kb_structured(query, retriever)

print("\n🔍 Raw KB Result:")
from pprint import pprint
pprint(result)

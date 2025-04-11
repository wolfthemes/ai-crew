from tools.kb_tools import search_kb_raw
from tools.vector_retriever import retriever

query = "how to update wpbakery in herion"

result = search_kb_raw(query, retriever)

print("\n🔍 Raw KB Result:")
from pprint import pprint
pprint(result)

from core.kb_searcher import KnowledgeBaseSearcher

def search_kb_structured(query, retriever=None, context: dict = None):
    searcher = KnowledgeBaseSearcher(retriever=retriever, context=context or {})
    return searcher.find_best_match(query)

def run_kb_research_debug(query, retriever=None, context: dict = None):
    from core.kb_searcher import KnowledgeBaseSearcher

    searcher = KnowledgeBaseSearcher(retriever=retriever, context=context or {})

    print(f"🔍 Running research for: {query}")
    result = searcher.find_best_match(query)

    print("\n=== MATCH BREAKDOWN ===")
    print(result)

    return result

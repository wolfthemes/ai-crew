from core.kb_searcher import KnowledgeBaseSearcher

def search_kb_structured(query, retriever=None, context: dict = None):
    searcher = KnowledgeBaseSearcher(retriever=retriever, context=context or {})
    return searcher.find_best_match(query)
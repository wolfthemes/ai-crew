from core.kb_searcher import KnowledgeBaseSearcher

def search_kb_raw(query, retriever=None):
    searcher = KnowledgeBaseSearcher(theme="generic", retriever=retriever)
    return searcher.find_best_match(query)
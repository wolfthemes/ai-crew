from core.kb_searcher import KnowledgeBaseSearcher

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

def search_kb_raw(query, retriever=None):
    searcher = KnowledgeBaseSearcher(theme="generic", retriever=retriever)
    return searcher.find_best_match(query)
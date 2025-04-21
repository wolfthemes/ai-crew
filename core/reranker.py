def rerank_results(results):
    """Sort results by priority type"""
    priority_map = {
        "common_issue": 1,
        "reference_ticket": 2, # not available yet
        "kb_article": 3,
        "support_ticket": 4,
        "theme_doc": 5
        
    }
    return sorted(results, key=lambda doc: priority_map.get(doc.metadata.get("source", ""), 99))
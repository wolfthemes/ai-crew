from core.reranker import rerank_results

class KnowledgeBaseSearcher:
    # Define source priority order - common_issue highest, theme_doc lowest
    SOURCE_PRIORITY = {
        "common_issue": 1,
        "reference_ticket": 2,
        "kb_article": 3,
        "support_ticket": 4,
        "theme_doc": 5,
        "theme_info": 6,
        "product_positioning": 7,
        "theme_meta": 8,
        "theme_changelog": 9,
        "product_wiki": 10,
        "unknown": 99
    }
    
    def __init__(self, retriever, context: dict):
        self.context = context
        self.retriever = retriever

    def find_best_match(self, query: str) -> dict:
        """Structured search using strict priority hierarchy and confidence scoring."""
        if not self.retriever:
            return {
                "source": "error",
                "title": "Retrieval Error",
                "content": "Retrieval is disabled. Vectorstore not loaded."
            }

        # Get initial results and rerank them
        results = rerank_results(self.retriever.invoke(query))

        if not results:
            return {
                "source": "none",
                "title": "No Results",
                "content": "No relevant results found in the knowledge base."
            }
        
        # First sort results by source priority
        prioritized_results = sorted(
            results, 
            key=lambda doc: self.SOURCE_PRIORITY.get(doc.metadata.get("source", "unknown"), 99)
        )
        
        # Group results by source type for easier processing
        source_groups = {}
        for doc in prioritized_results:
            source = doc.metadata.get("source", "unknown")
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(doc)
        
        # Process in priority order
        
        # 1. Common issues (highest priority)
        if "common_issue" in source_groups:
            best_match = source_groups["common_issue"][0]
            confidence = self._calculate_confidence(best_match, query)
            needs_customization = best_match.metadata.get("human_validation", False)
            
            return {
                "source": "common_issue",
                "title": best_match.metadata.get("title", "Common Issue"),
                "issue": best_match.metadata.get("issue", ""),
                "solution": best_match.metadata.get("solution", ""),
                "content": f"STRICT_RESPONSE: {best_match.metadata.get('solution', '')}" if confidence > 0.7 and not needs_customization else best_match.metadata.get('solution', ''),
                "plugin": best_match.metadata.get("plugin", []),
                "builder": best_match.metadata.get("builder", ""),
                "theme": best_match.metadata.get("theme", ""),
                "confidence_score": confidence,
                "requires_customization": needs_customization
            }
        
        # 2. Reference tickets
        if "reference_ticket" in source_groups:
            best_match = source_groups["reference_ticket"][0]
            confidence = self._calculate_confidence(best_match, query)
            needs_customization = best_match.metadata.get("human_validation", False)
            
            return {
                "source": "reference_ticket",
                "title": best_match.metadata.get("title", "Reference Ticket"),
                "issue": best_match.metadata.get("issue", ""),
                "solution": best_match.metadata.get("solution", ""),
                "content": f"STRICT_RESPONSE: {best_match.metadata.get('solution', '')}" if confidence > 0.7 and not needs_customization else best_match.metadata.get('solution', ''),
                "confidence_score": confidence,
                "requires_customization": needs_customization
            }
        
        # 3. KB articles
        if "kb_article" in source_groups:
            best_match = source_groups["kb_article"][0]
            confidence = self._calculate_confidence(best_match, query)
            
            return {
                "source": "kb_article",
                "title": best_match.metadata.get("title", "KB Article"),
                "url": best_match.metadata.get("url", ""),
                "content": best_match.page_content[:1000],
                "confidence_score": confidence,
                "is_strict": False
            }
        
        # 4. Support tickets
        if "support_ticket" in source_groups:
            best_match = source_groups["support_ticket"][0]
            
            return {
                "source": "support_ticket",
                "title": best_match.metadata.get("title", "Support Ticket"),
                "ticket_id": best_match.metadata.get("ticket_id", ""),
                "theme": best_match.metadata.get("theme", ""),
                "content": best_match.page_content[:1000],
                "confidence_score": 0.5,  # Lower confidence for support tickets
                "is_strict": False
            }
        
        # 5. Theme docs
        if "theme_doc" in source_groups or "theme_info" in source_groups:
            theme_docs = source_groups.get("theme_doc", []) + source_groups.get("theme_info", [])
            if theme_docs:
                best_match = theme_docs[0]
                
                return {
                    "source": best_match.metadata.get("source", "theme_doc"),
                    "title": best_match.metadata.get("title", "Theme Documentation"),
                    "slug": best_match.metadata.get("slug", ""),
                    "url": best_match.metadata.get("url", ""),
                    "content": best_match.page_content[:1000],
                    "confidence_score": 0.4,  # Lowest confidence for theme docs
                    "is_strict": False
                }
        
        # 6. Product positioning / theme meta / changelogs / wiki
        for source_key in ("product_positioning", "theme_meta", "theme_changelog", "product_wiki"):
            if source_key in source_groups:
                best_match = source_groups[source_key][0]
                confidence = self._calculate_confidence(best_match, query)
                return {
                    "source": source_key,
                    "title": best_match.metadata.get("title", "Theme Reference"),
                    "theme": best_match.metadata.get("theme", ""),
                    "url": best_match.metadata.get("url", ""),
                    "content": best_match.page_content[:1000],
                    "confidence_score": confidence,
                    "is_strict": False
                }

        # Fallback: first result if no categorized results
        first_result = prioritized_results[0]
        
        return {
            "source": first_result.metadata.get("source", "unknown"),
            "title": first_result.metadata.get("title", "Untitled"),
            "url": first_result.metadata.get("url", ""),
            "content": first_result.page_content[:1000],
            "confidence_score": 0.3,  # Very low confidence for uncategorized results
            "is_strict": False,
            "all_results": [
                {
                    "source": doc.metadata.get("source", "unknown"),
                    "title": doc.metadata.get("title", "Untitled"),
                    "url": doc.metadata.get("url", ""),
                    "snippet": doc.page_content[:300]
                }
                for doc in prioritized_results[1:3]
            ]
        }
    
    def _calculate_confidence(self, doc, query):
        """Calculate confidence score based on document source and query relevance"""
        # Base confidence by source type
        source = doc.metadata.get("source", "unknown")
        if source == "common_issue":
            base_confidence = 0.8
        elif source == "reference_ticket":
            base_confidence = 0.75
        elif source == "kb_article":
            base_confidence = 0.7
        elif source == "support_ticket":
            base_confidence = 0.5
        elif source in ["theme_doc", "theme_info"]:
            base_confidence = 0.4
        elif source in ["product_positioning", "theme_meta"]:
            base_confidence = 0.45
        elif source in ["theme_changelog", "product_wiki"]:
            base_confidence = 0.35
        else:
            base_confidence = 0.3
        
        # Add some simple relevance scoring (this could be enhanced with better matching)
        if query.lower() in doc.metadata.get("title", "").lower():
            relevance_boost = 0.15  # Big boost for title match
        elif query.lower() in doc.page_content.lower()[:500]:
            relevance_boost = 0.1   # Medium boost for content match in first part
        elif query.lower() in doc.page_content.lower():
            relevance_boost = 0.05  # Small boost for content match anywhere
        else:
            relevance_boost = 0
            
        # Cap at 0.95
        return min(base_confidence + relevance_boost, 0.95)
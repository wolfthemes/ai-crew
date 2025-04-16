import json
from core.ticket_parser import TicketParser
from tools.kb_tools import search_kb_structured
from tools.vector_retriever import retriever

def process_ticket_research(ticket_text: str, ticket_meta: dict = None) -> str:

    print( ticket_meta )
        
    if ticket_meta:
        parts = [ticket_meta.get("last_message", ticket_text)]
        context = {
            "theme": ticket_meta.get("theme"),
            "builder": ticket_meta.get("builder"),
            "match_source": ticket_meta.get("match_source"),
            "full_thread_sumary": ticket_meta.get("full_thread_sumary"),
        }
        results = []
        for part in parts:
            kb_match = search_kb_structured(part, retriever, context=context)
            results.append({
                "part": part,
                "match": kb_match
            })

        return json.dumps({
            "customer_name": ticket_meta.get("customer", "Customer"),
            "theme": ticket_meta.get("theme"),
            "url": ticket_meta.get("user_site"),
            "results": results
        }, indent=2)

    else:
        parser = TicketParser(ticket_text)
        parsed = parser.extract_all()

        results = []
        for part in parsed["parts"]:
            kb_match = search_kb_structured(part, retriever)
            results.append({
                "part": part,
                "match": kb_match
            })

    return json.dumps(results, indent=2)

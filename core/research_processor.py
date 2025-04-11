import json
from core.ticket_parser import TicketParser
from tools.kb_tools import search_kb_structured
from tools.vector_retriever import retriever

def process_ticket_research(ticket_text: str) -> str:
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

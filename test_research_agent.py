from tools.vector_retriever import retriever
from tools.kb_tools import run_kb_research_debug

ticket_query = "A got an issue with "

context = {
    "customer": "Test Customer",
    "ticket_id": 999,
    "instruction": ""
}

if __name__ == "__main__":
    result = run_kb_research_debug(
        query=ticket_query,
        retriever=retriever,
        context=context
    )

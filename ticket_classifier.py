
import re
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from utils.document_loaders import load_common_issues

load_dotenv()

# Define simple label categories
LABELS = [
    "common_issue",
    "server_issue",
    "bug",
    "customization",
    "info_gap",
    "unclear"
]

# Load vector store from common issues (can be expanded later)
embedding = OpenAIEmbeddings()
common_issues = load_common_issues()
vectorstore = FAISS.from_documents(common_issues, embedding)
retriever = vectorstore.as_retriever()

def classify_ticket(ticket_text: str) -> str:
    results = retriever.invoke(ticket_text)
    if not results:
        return "unclear"

    top_doc = results[0]
    score = top_doc.metadata.get("score", 0)

    if top_doc.metadata.get("issue_type") == "common_issue":
        return "common_issue"

    # Basic fuzzy heuristics
    ticket_lower = ticket_text.lower()

    if "theme broken" in ticket_lower or "not loading" in ticket_lower:
        return "bug"

    if "how to customize" in ticket_lower or "can you add" in ticket_lower:
        return "customization"

    if "don't know" in ticket_lower or "no idea how" in ticket_lower or "missing" in ticket_lower:
        return "info_gap"

    return "unclear"

if __name__ == "__main__":
    test_tickets = [
        "I'm missing woo templates but I don't know how to install it.",
        "Elementor editor not loading",
        "Can you add a second logo?",
        "Demo import stuck",
        "The header disappeared after saving",
        "How to update Slider Revolution?"
    ]

    for t in test_tickets:
        print(f"📝 {t}")
        print(f"🔎 Classified as: {classify_ticket(t)}\n")

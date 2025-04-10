
import re
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from utils.document_loaders import load_common_issues

# Load environment variables (API keys, etc.)
load_dotenv()

# Define label categories
LABELS = [
    "common_issue",
    "server_issue",
    "bug",
    "customization",
    "info_gap",
    "unclear"
]

# Load vector store from common issues
embedding = OpenAIEmbeddings()
common_issues = load_common_issues()
vectorstore = FAISS.from_documents(common_issues, embedding)

def split_ticket_into_parts(text: str) -> list[str]:
    # Split by sentence or paragraph
    parts = re.split(r"(?<=[.?!])\\s+|\\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 8]

def classify_ticket(ticket_text: str) -> str:
    results = vectorstore.similarity_search_with_score(ticket_text, k=1)

    if results:
        top_doc, score = results[0]
        top_issue_type = top_doc.metadata.get("issue_type")

        print(f"    ⚙️ Score: {score:.2f}")
        if top_issue_type == "common_issue" and score > 0.6:
            return "common_issue"

    # Fallback heuristics
    ticket_lower = ticket_text.lower()

    if "don't know" in ticket_lower or "no idea how" in ticket_lower:
        return "info_gap"

    if "missing" in ticket_lower and "template" in ticket_lower:
        return "info_gap"

    if "theme broken" in ticket_lower or "not loading" in ticket_lower:
        return "bug"

    if "how to customize" in ticket_lower or "can you add" in ticket_lower:
        return "customization"
    
    if "elementor" in ticket_lower and "not loading" in ticket_lower:
        return "common_issue"

    if "demo import" in ticket_lower or "can't import demo" in ticket_lower:
        return "common_issue"

    if "update slider" in ticket_lower or "slider revolution" in ticket_lower:
        return "common_issue"

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

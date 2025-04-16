from tools.kb_tools import search_kb_structured
from langchain.vectorstores import FAISS  # or your actual retriever setup
from langchain.embeddings import HuggingFaceEmbeddings  # adjust as needed
from langchain.docstore import InMemoryDocstore
import os

# Setup: Load vectorstore (adapt this part to your real setup)
def load_test_retriever():
    # If you're using FAISS locally
    if not os.path.exists("data/vectorstore"):
        raise FileNotFoundError("Vectorstore not found, make sure it's built first.")

    embeddings = HuggingFaceEmbeddings()
    vectorstore = FAISS.load_local("data/vectorstore", embeddings, docstore=InMemoryDocstore({}))
    return vectorstore.as_retriever()

# === Fake Ticket Context ===
ticket_query = "Vimeo video not showing on homepage"
ticket_theme = "Kayo"

context = {
    "theme": ticket_theme,
    "customer": "Test Customer",
    "ticket_id": 999,
    "instruction": "Please check the Kayo doc"
}

# === Run the research process ===
if __name__ == "__main__":
    retriever = load_test_retriever()

    result = search_kb_structured(
        query=ticket_query,
        retriever=retriever,
        context=context
    )

    import json
    print(json.dumps(result, indent=2))

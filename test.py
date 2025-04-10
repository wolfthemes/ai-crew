
import json
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from utils.document_loaders import (
    load_common_issues,
    load_theme_notes,
    load_theme_meta,
    load_kb_articles,
    load_theme_docs,
    load_closed_tickets
)

load_dotenv()

def rerank_results(results):
    priority_map = {
        "common_issue": 1,
        "kb_article": 2,
        "theme_note": 3,
        "theme_doc": 4,
        "support_ticket": 5
    }
    return sorted(results, key=lambda doc: priority_map.get(doc.metadata.get("source", ""), 99))

def main():
    print("Loading documents...")
    theme_notes = load_theme_notes()
    theme_meta_docs = load_theme_meta()
    articles = load_kb_articles()
    theme_docs = load_theme_docs()
    tickets = load_closed_tickets()
    common_issues = load_common_issues()
    all_docs = theme_meta_docs + theme_notes + common_issues + articles + theme_docs + tickets

    print(f"Loaded {len(all_docs)} documents.")

    embedding = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(all_docs, embedding)
    retriever = vectorstore.as_retriever()

    query = "Elementor editor not loading"
    print(f"Query: {query}")
    results = rerank_results(retriever.invoke(query))

    matches = [
        {
            "title": doc.metadata.get("title"),
            "expected_response": doc.metadata.get("expected_response")
        }
        for doc in results if doc.metadata.get("issue_type") == "common_issue"
    ]

    print("\nMatched Common Issues:")
    print(json.dumps(matches, indent=2))

if __name__ == "__main__":
    main()

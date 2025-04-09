# test_env.py
from crewai import Agent
from crewai_tools import ScrapeWebsiteTool
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document

docs = [Document(page_content="This is a test doc", metadata={"title": "Test", "source": "test"})]

embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embedding)

retriever = vectorstore.as_retriever()

def test_kb_search(query: str):
    results = retriever.invoke(query)
    for doc in results:
        print(doc.page_content)

agent = Agent(
    role="Test Agent",
    goal="Test FAISS and KB Search",
    backstory="You're just here to test things.",
    tools=[],
    verbose=True
)

test_kb_search("test")

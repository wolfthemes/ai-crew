from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from crewai import Agent
from crewai_tools import BaseTool
import json

# Custom wrapper for the retriever tool to make it CrewAI compatible
class KBSearchTool(BaseTool):
    name = "KB Search Tool"
    description = "Searches the WolfThemes Knowledge Base for answers to theme issues"

    def __init__(self, retriever):
        self.retriever = retriever

    def _run(self, query: str) -> str:
        results = self.retriever.invoke(query)
        return "\n\n".join([f"Title: {doc.metadata['title']}\nURL: {doc.metadata['url']}\nContent: {doc.page_content}" 
                          for doc in results])

# Load KB data
with open("data/wolfthemes_kb_articles.json", encoding="utf-8") as f:
    kb_data = json.load(f)

docs = [
    Document(
        page_content=article["content"],
        metadata={"title": article["title"], "url": article["url"]}
    ) for article in kb_data
]

# Embed and store in vector DB
embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embedding)
retriever = vectorstore.as_retriever()

# Create CrewAI-compatible tool
kb_tool = KBSearchTool(retriever)

# Create CrewAI agent
support_agent = Agent(
    role="WordPress Theme Support Expert",
    goal="Use the knowledge base to resolve customer tickets efficiently",
    backstory="""You are a WordPress support expert for WolfThemes with 
    access to detailed documentation. You use the knowledge base to find 
    accurate solutions for customers.""",
    tools=[kb_tool],
    allow_delegation=False,
    verbose=True
)
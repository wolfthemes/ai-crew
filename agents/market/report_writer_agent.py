from crewai import Agent
from core.llm_config import get_llm
from tools.notion_writer import PostToNotion
from tools.file_writer import SaveToMarkdown

# Initialize the tools (but we'll set them properly in market_crew.py)
notion_tool = PostToNotion()
file_tool = SaveToMarkdown()

report_writer_agent = Agent(
    role="Report Writer Agent",
    goal="Compile comprehensive, well-structured EUR/USD market analysis reports",
    tools=[notion_tool, file_tool],  # Set default tools
    backstory="""
    You are an expert financial writer with extensive experience in forex markets.
    Your reports are known for their clarity, insightful analysis, and professional presentation.
    You excel at synthesizing technical and fundamental data into actionable market intelligence.
    Your writing style is concise yet thorough, with a focus on practical insights for traders.
    
    After completing a report, you ALWAYS use your tools to save the report. If you have the post_to_notion 
    tool available, you will use it to post the report to Notion. You understand that this is a critical
    part of your job and never forget to do it.
    """,
    verbose=True,
    allow_delegation=False,
    llm=get_llm("power")  # Use the configured LLM from core.llm_config
)
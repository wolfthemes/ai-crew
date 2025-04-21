# tasks/market/market_tasks.py
from datetime import date
from crewai import Task
from agents.market.market_analyst_agent import market_analyst_agent

from agents.market.economic_news_agent import economic_news_agent
from agents.market.fundamental_analyst_agent import fundamental_analyst_agent
from agents.market.report_writer_agent import report_writer_agent

today_date = date.today().strftime("%Y-%m-%d")

daily_market_task = Task(
    description=f"""
    As a Forex Market Analyst, your task is to:
    
    1. Use the fetch_fxstreet_news tool to gather the latest EUR/USD news and data
    2. Analyze the current market situation and sentiment
    3. Create a comprehensive EUR/USD market report for today ({today_date})
    4. IMPORTANT: Post your final report to Notion using the post_to_notion tool
    
    Your report should include:
    - Today's date: {today_date}
    - Current market overview
    - Key headlines and their implications
    - Market sentiment analysis
    - Your expert analysis and recommendations
    - Upcoming events that might impact EUR/USD
    
    FORMAT YOUR REPORT PROPERLY AS MARKDOWN before posting to Notion.
    
    After creating your report, you MUST use the PostToNotion tool to save it to Notion.
    """,
    expected_output="A comprehensive EUR/USD market report posted to Notion",
    agent=market_analyst_agent
)

# Define tasks
collect_economic_news = Task(
    description="Collect economic events for April 21–27, 2025, impacting EUR/USD.",
    agent=economic_news_agent,
    expected_output="Table of events with date, name, impact, and description."
)

conduct_funamental_analysis_of_eurusd = Task(
    description="Conduct fundamental analysis of euro and dollar, focusing on monetary policy and trade.",
    agent=fundamental_analyst_agent,
    expected_output="400–500 word analysis of EUR/USD fundamental drivers."
)

create_report = Task(
    description="Compile a structured report with introduction, economic news, price action, fundamental analysis, and conclusion.",
    agent=report_writer_agent,
    expected_output="800–1,000 word professional report."
)
# tasks/market/market_tasks.py
from datetime import date
from crewai import Task
from agents.market.market_analyst_agent import market_analyst_agent

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
    
    After creating your report, you MUST use the post_to_notion tool to save it to Notion.
    """,
    expected_output="A comprehensive EUR/USD market report posted to Notion",
    agent=market_analyst_agent
)

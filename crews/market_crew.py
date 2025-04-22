from crewai import Crew, Process
from pathlib import Path
import sys
import os
import json
from datetime import date, timedelta

# Import agents
from agents.market.economic_news_agent import economic_news_agent
from agents.market.fundamental_analyst_agent import fundamental_analyst_agent 
from agents.market.technical_analyst_agent import technical_analyst_agent
from agents.market.sentiment_analyst_agent import sentiment_analyst_agent
from agents.market.report_writer_agent import report_writer_agent

# Import tasks
from tasks.market.market_tasks import (
    collect_fxstreet_news,
    analyze_technical_factors,
    conduct_fundamental_analysis,
    analyze_market_sentiment,
    create_weekly_report
)

# Tools import
from tools.notion_writer import PostToNotion
from tools.file_writer import SaveToMarkdown

def run_market_analysis(verbose=True, post_to_notion=True, save_to_file=True):
    """
    Run the market analysis crew to generate a comprehensive EUR/USD weekly report
    
    Args:
        verbose (bool): Whether to show detailed output
        post_to_notion (bool): Whether to post the final report to Notion
        save_to_file (bool): Whether to save the report to a markdown file
        
    Returns:
        The result from the crew execution (the final report)
    """
    
    # Initialize report saving directory if needed
    if save_to_file:
        os.makedirs("data/reports", exist_ok=True)
    
    # Current date information for file naming and report content
    today_date = date.today()
    today_date_str = today_date.strftime("%Y-%m-%d")
    
    # Initialize tools list for report writer
    report_writer_tools = []
    
    # Add tools based on parameters
    if post_to_notion:
        try:
            notion_tool = PostToNotion()
            if notion_tool.notion and notion_tool.database_id:
                report_writer_tools.append(notion_tool)
                print("✅ Notion posting tool initialized and ready")
            else:
                print("⚠️ Notion tool initialized but missing credentials")
        except Exception as e:
            print(f"⚠️ Failed to initialize Notion tool: {e}")
    
    if save_to_file:
        file_path = f"data/reports/eurusd_weekly_report_{today_date_str}.md"
        file_tool = SaveToMarkdown(default_path=file_path)
        report_writer_tools.append(file_tool)
        print("✅ File saving tool initialized")
    
    # Update report writer agent with tools
    if report_writer_tools:
        print(f"📝 Adding {len(report_writer_tools)} tools to report writer agent")
        for tool in report_writer_tools:
            print(f"   - {tool.name}: {tool.description[:60]}...")
        
        # This is the key line - make sure it's setting the tools correctly
        report_writer_agent.tools = report_writer_tools
    else:
        print("⚠️ No tools added to report writer agent")
    
    # Create the crew with all agents and tasks
    market_crew = Crew(
        agents=[
            economic_news_agent, 
            technical_analyst_agent,
            fundamental_analyst_agent,
            sentiment_analyst_agent,
            report_writer_agent
        ],
        tasks=[
            collect_fxstreet_news,
            analyze_technical_factors, 
            conduct_fundamental_analysis,
            analyze_market_sentiment,
            create_weekly_report
        ],
        process=Process.sequential,  # Tasks executed in order
        verbose=verbose,
        manager_llm=report_writer_agent.llm  # Use the same LLM for the manager
    )

    try:
        # Configure max tokens for larger outputs to ensure complete reports
        # This helps prevent truncation issues
        if hasattr(report_writer_agent.llm, 'max_tokens'):
            original_max_tokens = report_writer_agent.llm.max_tokens
            report_writer_agent.llm.max_tokens = 4096  # Ensure enough tokens for full report
        
        print("\n" + "="*50)
        print("🚀 STARTING EUR/USD WEEKLY MARKET ANALYSIS")
        print("="*50 + "\n")
        
        # Kick off the crew's work
        result = market_crew.kickoff()
        
        # Reset max tokens if we changed it
        if hasattr(report_writer_agent.llm, 'max_tokens') and 'original_max_tokens' in locals():
            report_writer_agent.llm.max_tokens = original_max_tokens
        
        print("\n" + "="*50)
        print("✅ EUR/USD WEEKLY MARKET ANALYSIS COMPLETE")
        print("="*50 + "\n")
        
        # Save metadata about the report execution
        if save_to_file:
            # Convert result to string for length measurement
            result_str = str(result)
            
            metadata = {
                "generated_on": today_date_str,
                "agents_used": [
                    "Economic News Agent",
                    "Technical Analyst Agent",
                    "Fundamental Analyst Agent",
                    "Sentiment Analyst Agent",
                    "Report Writer Agent"
                ],
                "posted_to_notion": post_to_notion,
                "report_length": len(result_str) if result else 0
            }
            
            metadata_path = f"data/reports/metadata_{today_date_str}.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📊 Report metadata saved to {metadata_path}")
        
        return result
    except Exception as e:
        print(f"❌ Error running market crew: {e}")
        import traceback
        traceback.print_exc()
        return None
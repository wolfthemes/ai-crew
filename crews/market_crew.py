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
from scripts.post_report_to_notion import post_report_to_notion

# Import tasks
from tasks.market.market_tasks import (
    collect_fxstreet_news,
    analyze_technical_factors,
    conduct_fundamental_analysis,
    analyze_market_sentiment,
    create_weekly_report
)

# Tools import
from tools.file_writer import SaveToMarkdown

def run_market_analysis(verbose=True, post_to_notion=True, save_to_file=True, period="weekly"):
    """
    Run the market analysis crew to generate a comprehensive EUR/USD market report
    
    Args:
        verbose (bool): Whether to show detailed output
        post_to_notion (bool): Whether to post the final report to Notion
        save_to_file (bool): Whether to save the report to a markdown file
        period (str): The period of the report - "daily" or "weekly"
        
    Returns:
        The result from the crew execution (the final report)
    """
    
    # Validate period parameter
    if period not in ["daily", "weekly"]:
        raise ValueError("Period must be either 'daily' or 'weekly'")
    
    # Initialize report saving directory if needed
    if save_to_file:
        folder_name = "daily_reports" if period == "daily" else "reports"
        os.makedirs(f"data/{folder_name}", exist_ok=True)
    
    # Current date information for file naming and report content
    today_date = date.today()
    today_date_str = today_date.strftime("%Y-%m-%d")
    
    # Initialize tools list for report writer
    # report_writer_tools = []
    
    # if save_to_file:
    #     folder_name = "daily_reports" if period == "daily" else "reports"
    #     file_name = f"eurusd_{period}_report_{today_date_str}.md"
    #     file_path = f"data/{folder_name}/{file_name}"
    #     file_tool = SaveToMarkdown(default_path=file_path)
    #     #report_writer_tools.append(file_tool)
    #     print(f"✅ File saving tool initialized for {period} report")
    
    # Update report writer agent with tools for file saving
    # if report_writer_tools:
    #     print(f"📝 Adding {len(report_writer_tools)} tools to report writer agent")
    #     for tool in report_writer_tools:
    #         print(f"   - {tool.name}: {tool.description[:60]}...")
        
    #     # Set the tools for the report writer agent
    #     report_writer_agent.tools = report_writer_tools
    # else:
    #     print("⚠️ No tools added to report writer agent")
    
    # Get appropriate tasks based on period
    if period == "daily":
        tasks = [
            # TODO: adapt task to daily report
            #collect_overnight_news,
            #analyze_intraday_technicals,
            #identify_key_levels,
            #create_daily_report
        ]
    else:  # weekly
        tasks = [
            collect_fxstreet_news,
            analyze_technical_factors, 
            conduct_fundamental_analysis,
            analyze_market_sentiment,
            create_weekly_report
        ]
    
    # Create the crew with all agents and tasks
    market_crew = Crew(
        agents=[
            economic_news_agent, 
            technical_analyst_agent,
            fundamental_analyst_agent,
            sentiment_analyst_agent,
            report_writer_agent
        ],
        tasks=tasks,
        process=Process.sequential,  # Tasks executed in order
        verbose=verbose,
        manager_llm=report_writer_agent.llm  # Use the same LLM for the manager
    )

    try:
        # Configure max tokens for larger outputs to ensure complete reports
        # This helps prevent truncation issues
        if hasattr(report_writer_agent.llm, 'max_tokens'):
            original_max_tokens = report_writer_agent.llm.max_tokens
            # Weekly reports need more tokens than daily
            max_tokens = 4096 if period == "weekly" else 2048
            report_writer_agent.llm.max_tokens = max_tokens
        
        print("\n" + "="*50)
        print(f"🚀 STARTING EUR/USD {period.upper()} MARKET ANALYSIS")
        print("="*50 + "\n")
        
        # Kick off the crew's work
        result = market_crew.kickoff()
        
        # Reset max tokens if we changed it
        if hasattr(report_writer_agent.llm, 'max_tokens') and 'original_max_tokens' in locals():
            report_writer_agent.llm.max_tokens = original_max_tokens
        
        print("\n" + "="*50)
        print(f"✅ EUR/USD {period.upper()} MARKET ANALYSIS COMPLETE")
        print("="*50 + "\n")
        
        # Save metadata about the report execution
        if save_to_file:
            # Convert result to string for length measurement
            result_str = str(result)
            
            metadata = {
                "generated_on": today_date_str,
                "report_type": period,
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
            
            folder_name = "daily_reports" if period == "daily" else "reports"
            metadata_path = f"data/{folder_name}/metadata_{today_date_str}.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📊 {period.capitalize()} report metadata saved to {metadata_path}")
        
        # Now post to Notion AFTER the report is generated
        if post_to_notion:
            try:
                print("\n" + "="*50)
                print(f"📄 POSTING {period.upper()} REPORT TO NOTION")
                folder_name = "daily_reports" if period == "daily" else "reports"
                file_name = f"eurusd_{period}_report_{today_date_str}.md"
                file_path = f"data/{folder_name}/{file_name}"
                notion_result = post_report_to_notion(
                    file_path=file_path,
                    title=f"EUR/USD {period.capitalize()} Report – {today_date_str}"
                )
                if notion_result:
                    print(f"✅ Successfully posted {period} report to Notion")
                else:
                    print(f"❌ Failed to post {period} report to Notion")
                print("="*50 + "\n")
            except Exception as e:
                print(f"❌ Error posting to Notion: {e}")
        
        return result
    except Exception as e:
        print(f"❌ Error running {period} market crew: {e}")
        import traceback
        traceback.print_exc()
        return None
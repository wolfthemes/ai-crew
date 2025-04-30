from crewai import Crew, Process
from pathlib import Path
import sys
import os
import json
from datetime import date, datetime, timedelta
import pytz

# Import agents
from agents.market.economic_news_agent import economic_news_agent
from agents.market.fundamental_analyst_agent import fundamental_analyst_agent 
from agents.market.technical_analyst_agent import technical_analyst_agent
from agents.market.sentiment_analyst_agent import sentiment_analyst_agent
from agents.market.weekly_report_writer_agent import weekly_report_writer_agent


from agents.market.daily_report_writer_agent import daily_report_writer_agent
from agents.market.session_analyst_agent import session_analyst_agent
from agents.market.weekly_profile_analyst_agent import weekly_profile_analyst_agent
from agents.market.daily_bias_analyst_agent import daily_bias_analyst_agent
from agents.market.cisd_pattern_analyst_agent import cisd_pattern_analyst_agent
from scripts.post_report_to_notion import post_report_to_notion

# Import tasks
from tasks.market.weekly_report_tasks import (
    collect_fxstreet_news,
    analyze_technical_factors,
    conduct_fundamental_analysis,
    analyze_market_sentiment,
    create_weekly_report
)

from tasks.market.daily_report_tasks import (
    collect_daily_news,
    analyze_weekly_profile,
    analyze_daily_bias,
    analyze_cisd_patterns,
    create_daily_report
)

# Tools import
from tools.file_writer import SaveToMarkdown
from utils.fxstreet_events_downloader import get_fxstreet_events
from utils.pdf_framework_reader import DailyBiasFramework

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
        folder_name = "daily" if period == "daily" else "weekly"
        os.makedirs(f"data/reports/{folder_name}", exist_ok=True)
    
    # Current date information for file naming and report content
    paris_tz = pytz.timezone('Europe/Paris')
    paris_now = datetime.now(paris_tz)
    today_date = paris_now.date()
    today_date_str = today_date.strftime("%Y-%m-%d")
    
    # Initialize tools list for report writer
    report_writer_tools = []
    
    if save_to_file:
        folder_name = "daily" if period == "daily" else "weekly"
        file_name = f"eurusd_{period}_report_{today_date_str}.md"
        file_path = f"data/reports/{folder_name}/{file_name}"
        file_tool = SaveToMarkdown(default_path=file_path)
        report_writer_tools.append(file_tool)
        print(f"✅ File saving tool initialized for {period} report")
    
    # Update report writer agent with tools for file saving
    if report_writer_tools:
        print(f"📝 Adding {len(report_writer_tools)} tools to report writer agent")
        for tool in report_writer_tools:
            print(f"   - {tool.name}: {tool.description[:60]}...")
        
        # Set the tools for the report writer agent
        weekly_report_writer_agent.tools = report_writer_tools
        daily_report_writer_agent.tools = report_writer_tools
    else:
        print("⚠️ No tools added to report writer agent")
    
    # Pre-fetch economic events and trading frameworks for context
    economic_events_context = None
    framework_context = None
    
    if period == "daily":
        # Load trading frameworks from PDFs
        try:
            print("📚 Loading trading frameworks from PDFs...")
            framework_reader = DailyBiasFramework()
            framework_context = framework_reader.get_all_frameworks_context()
            print("✅ Loaded trading frameworks")
        except Exception as e:
            print(f"⚠️ Error loading trading frameworks: {e}")
            framework_context = "Unable to load trading frameworks."
        
        # Fetch economic events
        try:
            print("📊 Pre-fetching economic events for context...")
            economic_events = get_fxstreet_events()
            economic_events_context = f"Economic events for this week: {json.dumps(economic_events)}"
            print(f"✅ Fetched {len(economic_events)} economic events")
        except Exception as e:
            print(f"⚠️ Error fetching economic events: {e}")
            economic_events_context = "Unable to fetch economic events."
            
        # Combine contexts
        if framework_context and economic_events_context:
            combined_context = f"{framework_context}\n\n{economic_events_context}"
        else:
            combined_context = framework_context or economic_events_context or ""
        
        # Use combined context
        economic_events_context = combined_context
    
    # Get appropriate tasks based on period
    if period == "daily":
        # For daily reports, we use the session analyst for daily bias analysis
        tasks = [
            collect_daily_news,
            analyze_weekly_profile,
            analyze_daily_bias,
            analyze_cisd_patterns,
            create_daily_report
        ]

        # Create the agent list based on period
        agents = [
            economic_news_agent,
            weekly_profile_analyst_agent,
            daily_bias_analyst_agent,
            cisd_pattern_analyst_agent,
            daily_report_writer_agent
        ]
    else:  # weekly
        tasks = [
            collect_fxstreet_news,
            analyze_technical_factors, 
            conduct_fundamental_analysis,
            analyze_market_sentiment,
            create_weekly_report
        ]
    
        # Create the agent list based on period
        agents = [
            economic_news_agent, 
            technical_analyst_agent,
            weekly_report_writer_agent
        ]
    
    if period == "weekly":
        agents.extend([
            fundamental_analyst_agent,
            sentiment_analyst_agent
        ])
    elif period == "daily" and session_analyst_agent:
        agents.append(session_analyst_agent)
    
    # Create the crew with all agents and tasks
    market_crew = Crew(
        agents=agents,
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
        if period == "daily":
            print(f"📅 Report Date: {today_date_str}")
            print(f"🕗 Generated at: {paris_now.strftime('%H:%M')} Paris Time")
            print(f"🎯 Focus: London Session")
        print("="*50 + "\n")
        
        # Kick off the crew's work
        result = market_crew.kickoff()
        
        # Reset max tokens if we changed it
        if hasattr(report_writer_agent.llm, 'max_tokens') and 'original_max_tokens' in locals():
            report_writer_agent.llm.max_tokens = original_max_tokens
        
        print("\n" + "="*50)
        print(f"✅ EUR/USD {period.upper()} MARKET ANALYSIS COMPLETE")
        print("="*50 + "\n")
        
        # Manually save the report to file if save_to_file is True
        if save_to_file and result:
            folder_name = "daily" if period == "daily" else "weekly"
            file_name = f"eurusd_{period}_report_{today_date_str}.md"
            file_path = f"data/reports/{folder_name}/{file_name}"
            
            # Write the report content to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(result))
                
            print(f"📝 Report saved to {file_path}")
        
        # Save metadata about the report execution
        if save_to_file:
            # Convert result to string for length measurement
            result_str = str(result)
            
            # Build the metadata based on period
            metadata = {
                "generated_on": today_date_str,
                "report_type": period,
                "posted_to_notion": post_to_notion,
                "report_length": len(result_str) if result else 0,
                "report_file_path": f"data/{folder_name}/{file_name}" if result else None
            }
            
            # Add period-specific metadata
            if period == "daily":
                metadata.update({
                    "session_focus": "London",
                    "generation_time": paris_now.strftime('%H:%M'),
                    "agents_used": [
                        "Economic News Agent",
                        "Technical Analyst Agent",
                        "Session Analyst Agent",
                        "Report Writer Agent"
                    ]
                })
            else:  # weekly
                metadata.update({
                    "agents_used": [
                        "Economic News Agent",
                        "Technical Analyst Agent",
                        "Fundamental Analyst Agent",
                        "Sentiment Analyst Agent",
                        "Report Writer Agent"
                    ]
                })
            
            folder_name = "daily" if period == "daily" else "weekly"
            metadata_path = f"data/reports/{folder_name}/metadata_{today_date_str}.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📊 {period.capitalize()} report metadata saved to {metadata_path}")
        
        # Now post to Notion AFTER the report is generated
        if post_to_notion:
            try:
                print("\n" + "="*50)
                print(f"📄 POSTING {period.upper()} REPORT TO NOTION")
                folder_name = "daily" if period == "daily" else "weekly"
                file_name = f"eurusd_{period}_report_{today_date_str}.md"
                file_path = f"data/reports/{folder_name}/{file_name}"
                
                # Create a title based on period
                if period == "daily":
                    title = f"EUR/USD Daily Report (London Session) – {today_date_str}"
                else:
                    title = f"EUR/USD Weekly Report – {today_date_str}"
                    
                notion_result = post_report_to_notion(
                    file_path=file_path,
                    title=title
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

if __name__ == "__main__":
    # This allows running the market crew directly with python market_crew.py
    # You can specify the period with a command line argument
    # Example: python market_crew.py daily
    period = "weekly"  # Default period
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["daily", "weekly"]:
        period = sys.argv[1].lower()
    
    print(f"Running {period} market analysis...")
    run_market_analysis(verbose=True, post_to_notion=True, save_to_file=True, period=period)
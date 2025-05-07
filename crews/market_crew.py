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
from agents.market.daily_report_writer_agent import daily_report_writer_agent
from agents.market.weekly_report_writer_agent import weekly_report_writer_agent
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
    #analyze_cisd_patterns,
    create_daily_report
)

# Tools import
from tools.file_writer import SaveToMarkdown
from utils.fxstreet_events_downloader import get_fxstreet_events
#from utils.pdf_framework_reader import DailyBiasFramework
from utils.weekly_report_reader import WeeklyReportReader
from utils.market_tools_integration import MarketToolsIntegration
from utils.market_utils import is_tradable_day

def run_market_analysis(verbose=True, post_to_notion=True, save_to_file=True, period="weekly", force=False):
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
    
    # Current date information for file naming and report content
    paris_tz = pytz.timezone('Europe/Paris')
    paris_now = datetime.now(paris_tz)
    today_date = paris_now.date()
    today_date_str = today_date.strftime("%Y-%m-%d")
    
    # Initialize report saving directory if needed
    if save_to_file:
        folder_name = "daily" if period == "daily" else "weekly"
        os.makedirs(f"data/reports/{folder_name}", exist_ok=True)
        
    # Initialize tools list for report writer
    report_writer_tools = []

    # Initialize market tools integration
    market_tools = None
    enhance_agents = True
    
    try:
        print("🧠 Initializing market tools integration...")
        market_tools = MarketToolsIntegration()
        
        # Don't append tools directly here - we'll add them to agents later
        # through the enhance_agent function
        enhance_agents = market_tools is not None
        
        if market_tools:
            available_tools = market_tools.get_available_tools()
            tools_str = ", ".join([t.name for t in available_tools])
            print(f"✅ Available market tools: {tools_str}")
        
    except Exception as e:
        print(f"⚠️ Error initializing market tools: {e}")
        market_tools = None


    # Fetch economic events to check if today is tradable (for daily reports only)
    economic_events = None
    tradable_day = True
    
    if period == "daily":
        try:
            print("📊 Pre-fetching economic events for tradable day check...")
            economic_events = get_fxstreet_events()
            #tradable_day = is_tradable_day(today_date, economic_events)
            #tradable_day = True
            if not force:
                tradable_day = is_tradable_day(today_date, economic_events)
            else:
                tradable_day = True
            
            if not tradable_day:
                print(f"⚠️ {today_date_str} is not a tradable day. Daily report generation skipped.")
                return None
            else:
                print(f"✅ {today_date_str} is a tradable day. Proceeding with daily report generation.")
        except Exception as e:
            print(f"⚠️ Error checking tradable day: {e}")
            # Continue anyway if we can't check
    
    # Set up file saving tools
    if save_to_file:
        folder_name = "daily" if period == "daily" else "weekly"
        file_name = f"eurusd_{period}_report_{today_date_str}.md"
        file_path = f"data/reports/{folder_name}/{file_name}"
        file_tool = SaveToMarkdown(default_path=file_path)
        report_writer_tools = [file_tool]  # Start with just the file tool
        print(f"✅ File saving tool initialized for {period} report")
    else:
        report_writer_tools = []  # Empty list if not saving to file
    
    # Add market tools if available
    if market_tools:
        # Get all available tools from market_tools
        available_tools = market_tools.get_available_tools()
        if available_tools:
            report_writer_tools.extend(available_tools)
            print(f"✅ Added {len(available_tools)} market tools to report writer")
    
    # Get appropriate report writer agent based on period
    report_writer_agent = daily_report_writer_agent if period == "daily" else weekly_report_writer_agent
    
    # Update report writer agent with tools for file saving
    if report_writer_tools:
        print(f"📝 Adding {len(report_writer_tools)} tools to report writer agent")
        for tool in report_writer_tools:
            print(f"   - {tool.name}: {tool.description[:60] if hasattr(tool, 'description') else 'No description'}")
        
        # Set the tools for the report writer agent
        report_writer_agent.tools = report_writer_tools
    else:
        print("⚠️ No tools added to report writer agent")
    
    # Pre-fetch economic events and trading frameworks for context
    economic_events_context = None
    framework_context = None
    weekly_report_context = None
    
    if period == "daily":
        # Get context from most recent weekly report
        try:
            print("📚 Loading most recent weekly report for context...")
            weekly_report_reader = WeeklyReportReader()
            weekly_report_metadata = weekly_report_reader.get_weekly_report_metadata()
            
            weekly_report_context = f"""
            Most recent weekly report date: {weekly_report_metadata['report_date']}
            Fundamental outlook: {weekly_report_metadata['fundamental_outlook']}
            Technical bias: {weekly_report_metadata['technical_bias']}
            Key levels: {json.dumps(weekly_report_metadata['key_levels'])}
            """
            print("✅ Loaded weekly report context")
        except Exception as e:
            print(f"⚠️ Error loading weekly report context: {e}")
            weekly_report_context = "Unable to load weekly report context."
        
        # Load trading frameworks from PDFs
        # try:
        #     print("📚 Loading trading frameworks from PDFs...")
        #     framework_reader = DailyBiasFramework()
        #     framework_context = framework_reader.get_all_frameworks_context()
        #     print("✅ Loaded trading frameworks")
        # except Exception as e:
        #     print(f"⚠️ Error loading trading frameworks: {e}")
        #     framework_context = "Unable to load trading frameworks."
        
        # Fetch economic events
        try:
            print("📊 Pre-fetching economic events for context...")
            if economic_events is None:  # Only fetch if not already fetched
                economic_events = get_fxstreet_events()
            economic_events_context = f"Economic events for this week: {json.dumps(economic_events)}"
            print(f"✅ Fetched {len(economic_events)} economic events")
        except Exception as e:
            print(f"⚠️ Error fetching economic events: {e}")
            economic_events_context = "Unable to fetch economic events."
            
        # Combine contexts
        combined_context = ""
        
        if weekly_report_context:
            combined_context += weekly_report_context + "\n\n"
        if framework_context:
            combined_context += framework_context + "\n\n"
        if economic_events_context:
            combined_context += economic_events_context
            
        # Use combined context
        economic_events_context = combined_context if combined_context else None
    
    # Get appropriate tasks and agents based on period
    if period == "daily":
        # For daily reports, we use the session analyst for daily bias analysis
        tasks = [
            collect_daily_news,
            analyze_weekly_profile,
            analyze_daily_bias,
            #analyze_cisd_patterns,
            create_daily_report
        ]

        # Create the agent list based on period
        agents = [
            economic_news_agent,
            weekly_profile_analyst_agent,
            daily_bias_analyst_agent,
            #cisd_pattern_analyst_agent,
            daily_report_writer_agent
        ]
        
        # Add session analyst if available
        if session_analyst_agent:
            agents.append(session_analyst_agent)
            
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
            weekly_report_writer_agent,
            fundamental_analyst_agent,
            sentiment_analyst_agent
        ]
    
    # Enhance agents with knowledge context if available
    if enhance_agents and market_tools:
        print("🧠 Enhancing agents with knowledge context...")
        
        # Map agent instances to their types
        agent_types = {
            weekly_profile_analyst_agent: 'weekly_profile',
            daily_bias_analyst_agent: 'daily_bias',
            technical_analyst_agent: 'technical',
            fundamental_analyst_agent: 'fundamental',
            sentiment_analyst_agent: 'sentiment',
            daily_report_writer_agent: 'report_writer',
            weekly_report_writer_agent: 'report_writer'
        }
        
        # Enhance each agent in the list
        for i, agent in enumerate(agents):
            if agent in agent_types:
                agent_type = agent_types[agent]
                try:
                    agents[i] = market_tools.enhance_agent(agent, agent_type)
                    print(f"✅ Enhanced {agent.role} with {agent_type} knowledge context")
                except Exception as e:
                    print(f"⚠️ Error enhancing {agent.role}: {e}")
    
    # Create the crew with all agents and tasks
    market_crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,  # Tasks executed in order
        verbose=verbose,
        memory=True,
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
                "report_file_path": f"data/{folder_name}/{file_name}" if result else None,
                "tradable_day": tradable_day
            }
            
            # Add period-specific metadata
            if period == "daily":
                metadata.update({
                    "session_focus": "London",
                    "generation_time": paris_now.strftime('%H:%M'),
                    "agents_used": [
                        "Economic News Agent",
                        "Weekly Profile Analyst Agent",
                        "Daily Bias Analyst Agent",
                        "CISD Pattern Analyst Agent",
                        "Daily Report Writer Agent"
                    ]
                })
            else:  # weekly
                metadata.update({
                    "agents_used": [
                        "Economic News Agent",
                        "Technical Analyst Agent",
                        "Fundamental Analyst Agent",
                        "Sentiment Analyst Agent",
                        "Weekly Report Writer Agent"
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
                    title=title,
                    period=period
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
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["daily", "weekly"]:
            period = sys.argv[1].lower()
    
    print(f"Running {period} market analysis...")
    run_market_analysis(verbose=True, post_to_notion=True, save_to_file=True, period=period)
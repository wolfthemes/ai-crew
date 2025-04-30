# tasks/market/daily_report_tasks.py
from datetime import date, datetime, timedelta
import pytz
from crewai import Task

# Import agents - this ensures the agents are available for assignment
from agents.market.cisd_pattern_analyst_agent import cisd_pattern_analyst_agent
from agents.market.economic_news_agent import economic_news_agent
from agents.market.weekly_profile_analyst_agent import weekly_profile_analyst_agent
from agents.market.session_analyst_agent import session_analyst_agent
from agents.market.daily_bias_analyst_agent import daily_bias_analyst_agent
from agents.market.daily_report_writer_agent import daily_report_writer_agent

# Calculate relevant dates
paris_tz = pytz.timezone('Europe/Paris')
paris_now = datetime.now(paris_tz)
today_date = paris_now.date()
yesterday_date = today_date - timedelta(days=1)
today_str = today_date.strftime("%Y-%m-%d")
yesterday_str = yesterday_date.strftime("%Y-%m-%d")

# Define tasks with explicit agent assignments
collect_daily_news = Task(
    description=f"""
    Collect and analyze the latest EUR/USD news from the past 24 hours, focusing on events that will impact today's London session.
    
    Focus on:
    1. Economic data releases for both EUR and USD from yesterday ({yesterday_str})
    2. Any early morning news from today ({today_str})
    3. Upcoming high-impact events scheduled for today's London session
    4. Market reactions to recent events
    
    Create two separate sections in your analysis:
    
    SECTION 1: RECENT NEWS IMPACT
    - Economic events from yesterday and early today
    - Market reactions to these events
    - Surprises or deviations from expectations
    
    SECTION 2: TODAY'S SCHEDULED EVENTS
    - Create a table of events scheduled for today with:
      * Time (London session timezone)
      * Currency affected (EUR or USD)
      * Event name
      * Expected impact (High, Medium, Low)
      * Previous reading and forecast if available
    
    Use the get_fxstreet_events utility function to retrieve the current week's economic events
    and filter for those relevant to today's trading session.
    
    Focus only on news that is likely to directly impact today's London session trading.
    """,
    expected_output="""
    A concise analysis of recent EUR/USD news with:
    1. Yesterday's key events and their market impact
    2. Any early morning news affecting today's bias
    3. A table of today's scheduled events during London hours
    4. An overall assessment of how news is likely to affect today's trading session
    
    The analysis should be actionable and specifically focused on the London session.
    """,
    agent=economic_news_agent,
    async_execution=False
)

analyze_weekly_profile = Task(
    description=f"""
    Analyze EUR/USD to determine the current weekly profile pattern and how it impacts today's ({today_str}) London session bias.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. WEEKLY PROFILE IDENTIFICATION
       - Current weekly profile classification (Classic Expansion, Consolidation Reversal, or Midweek Reversal)
       - Assessment of Monday-Tuesday price action
       - How Wednesday's action confirms or changes the profile
       - Projected development for the remainder of the week
    
    2. PROFILE-SPECIFIC CHARACTERISTICS
       - Key characteristics of the identified weekly profile
       - Typical progression of the identified pattern
       - High-probability days within the current profile
       - Potential reversal points based on profile structure
    
    3. WEEKLY RANGE DEVELOPMENT
       - Current week's range relative to previous week
       - Range expansion or consolidation assessment
       - Key range boundaries and potential extension targets
    
    4. TODAY'S SESSION CONTEXT
       - How today's London session fits within the weekly profile
       - Session-specific probabilities based on the current day of week
       - Optimal trading approach given the weekly context
       - Key levels to monitor for profile confirmation or invalidation
    
    Provide specific references to scenarios illustrated in the Weekly Profile Guide when applicable.
    Focus on practical, actionable insights for today's London session.
    """,
    expected_output="""
    A comprehensive analysis of EUR/USD's current weekly profile with:
    1. Clear weekly profile identification
    2. Detailed profile characteristics
    3. Weekly range development assessment
    4. Today's London session context within the weekly profile
    
    The analysis should be data-driven and immediately actionable for a London session trader.
    """,
    agent=weekly_profile_analyst_agent,
    async_execution=False
)

analyze_daily_bias = Task(
    description=f"""
    Analyze EUR/USD using the Daily Bias framework to determine the directional bias for today's London session ({today_str}).
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. PREVIOUS DAY HIGH & LOW
       - Previous day's high, low, open, close prices
       - Analysis of how these levels might function as liquidity draws
       - Potential for reversals framed off PDH and PDL
    
    2. PREVIOUS WEEK HIGH & LOW
       - How current price relates to previous week's range
       - Potential for weekly range expansion or contraction
    
    3. SWING POINTS
       - Identification of significant swing highs and lows
       - Assessment of potential liquidity draws at these points
       - Framework for reversals off key swing points
    
    4. FAILURE TO DISPLACE
       - Analysis of any failure to displace over old highs/lows
       - How these failures might frame potential reversals
    
    5. NEXT DAY MODEL
       - Apply the Next Day Model based on previous day's close position
       - Determine immediate directional bias (bullish/bearish/neutral)
       - Calculate confidence level based on close extremity
       - Identify key price targets based on the model
    
    Your analysis should be detailed, precise, and actionable, with specific price levels mentioned throughout.
    Focus on creating a clear bias directive for trading the London session today.
    """,
    expected_output="""
    A comprehensive analysis of today's EUR/USD London session trading bias with:
    1. Clear directional bias statement with confidence level
    2. Specific price levels for the Previous Day High & Low
    3. Analysis of Previous Week High & Low relevance
    4. Identification of key Swing Points
    5. Assessment of any Failure To Displace scenarios
    6. Next Day Model application and projection
    
    The analysis should be data-driven and immediately actionable for a London session trader.
    """,
    agent=daily_bias_analyst_agent,
    async_execution=False
)

analyze_cisd_patterns = Task(
    description=f"""
    Analyze the current M30 and M5 charts for EUR/USD to identify potential CISD patterns
    for today's London session trading on {today_str}.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. M30 CISD IDENTIFICATION
       - Current Change in State of Delivery on M30 timeframe
       - Key breaker blocks, order blocks, and fair value gaps
       - Direction bias relative to daily trend
       - Key levels within the CISD range (support/resistance points)
    
    2. M5 ENTRY PATTERN SETUP
       - Potential M5 CISD formation zones
       - Optimal entry criteria within the M30 CISD range
       - Trigger conditions for entry execution
       - Confirmation signals for direction validation
    
    3. DAILY BIAS ALIGNMENT
       - How the current CISD aligns with the Daily Bias framework
       - Previous Day High & Low analysis
       - Failure to Displace considerations
       - Next Day Model application
    
    4. WEEKLY PROFILE CONTEXT
       - Current weekly profile classification (classic expansion, consolidation reversal, or midweek reversal)
       - Key pattern characteristics observed this week
       - How today's CISD fits into the weekly structure
    
    5. PROBABILITY ASSESSMENT
       - Confidence rating for identified patterns
       - Alignment with daily/weekly bias direction
       - Time window considerations for optimal execution (09:30-11:00 London)
    
    Focus specifically on identifying actionable patterns for the 09:30-11:00 London
    entry window, with clear entry, stop and target parameters.
    """,
    expected_output="""
    Detailed analysis of current CISD pattern opportunities with:
    1. Clear identification of active M30 CISD patterns
    2. Specific M5 entry zones within these patterns
    3. Precise price levels for entry, stop and targets
    4. Daily Bias framework alignment
    5. Weekly profile context
    6. Probability assessment for pattern completion
    
    The analysis should be immediately actionable for London session trading.
    """,
    agent=cisd_pattern_analyst_agent,
    async_execution=False
)

create_daily_report = Task(
    description=f"""
    Compile a comprehensive EUR/USD daily market report for the London session on {today_str}.
    
    YOUR REPORT MUST INCLUDE THE FOLLOWING SECTIONS:
    
    1. TITLE: "EUR/USD Daily Report (London Session) – {today_str}"
    
    2. EXECUTIVE SUMMARY (100-150 words)
       - Session bias statement (bullish/bearish/neutral) with confidence level
       - Key price levels for today (previous day high/low, key targets)
       - Major news impact assessment
       - Trading viability assessment (high/medium/low probability environment)
    
    3. RECENT NEWS ANALYSIS (200-250 words)
       - Summary of yesterday's events and their impact
       - Early morning developments
       - Today's scheduled high-impact events
       - News-based market sentiment assessment
    
    4. SESSION BIAS ANALYSIS (300-350 words)
       - Next Day Model application and results
       - Technical assessment of current conditions
       - Volatility and trend metrics (ATR, Choppiness Index)
       - London session-specific probabilities
    
    5. SESSION TRADING FRAMEWORK (200-250 words)
       - Sequential decision tree for trading approach
       - Specific entry criteria and levels
       - Target levels with clear price points
       - Stop placement and risk management
    
    6. ACTION PLAN (100-150 words)
       - Concrete, actionable trading guidance
       - Timeframe-specific approach
       - Key decision points during the session
       - Final recommendation
    
    FORMATTING REQUIREMENTS:
    - Use proper Markdown formatting with headers, lists, tables
    - Make key levels and price targets stand out (bold)
    - Include section headers and sub-sections for readability
    - Ensure the report is well-structured and professional
    - Report should be concise but comprehensive, approximately 900-1200 words total
    
    IMPORTANT:
    - Be specific with price levels, times, and targets
    - Focus specifically on the London session (08:00-16:00 London time)
    - Explicitly reference the Daily Bias framework and Next Day model
    - Provide actionable, time-specific insights for traders
    - Ensure all analysis is data-driven and well-reasoned
    - This is a PROFESSIONAL report - avoid vague language and ensure all claims are substantiated
    """,
    expected_output="""
    Complete, professional EUR/USD daily market report for the London session in properly formatted Markdown,
    approximately 900-1200 words with all sections fully completed.
    
    The report should provide clear, actionable trading guidance specifically for today's London session,
    with explicit references to the Daily Bias framework and Next Day model.
    """,
    agent=daily_report_writer_agent,
    async_execution=False
)
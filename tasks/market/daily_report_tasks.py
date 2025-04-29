# tasks/market/daily_report_tasks.py
from datetime import date, datetime, timedelta
import pytz
from crewai import Task

# Import agents - this ensures the agents are available for assignment
from agents.market.economic_news_agent import economic_news_agent  
from agents.market.technical_analyst_agent import technical_analyst_agent
from agents.market.session_analyst_agent import session_analyst_agent
from agents.market.report_writer_agent import report_writer_agent

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

analyze_daily_bias = Task(
    description=f"""
    Analyze today's EUR/USD trading bias for the London session ({today_str}) using the Daily Bias framework and Next Day model.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. PREVIOUS DAY ANALYSIS
       - Previous day's high, low, open, close prices
       - Range calculation and assessment
       - Close position within the daily range
    
    2. NEXT DAY MODEL APPLICATION
       - Apply the Next Day Model based on previous day's close position
       - Determine immediate directional bias (bullish/bearish/neutral)
       - Calculate confidence level based on close extremity
       - Identify key price targets based on the model
    
    3. CURRENT TECHNICAL ASSESSMENT
       - Current price relative to previous day's range
       - H4 chart trend direction
       - Key support/resistance levels
       - Volatility assessment using ATR
       - Choppiness Index reading to determine trend vs. ranging conditions
    
    4. LONDON SESSION FRAMEWORK
       - Explicit London session bias statement (bullish/bearish/neutral)
       - Confidence level assessment (high/medium/low)
       - Key levels for session entries and exits
       - Potential price targets for the session
       - Risk management parameters
    
    5. SEQUENTIAL DECISION TREE
       - Create a step-by-step trading plan for the session
       - Specify confirmation and invalidation levels
       - Provide multiple scenarios based on early price action
    
    6. PDF FRAMEWORK IMPLEMENTATION
       - Reference concepts from the Daily Bias PDF framework
       - Apply the Weekly Profile concept if relevant
       - Utilize specific terminology from the framework documents
       - Clearly mark when you're applying framework-specific concepts
    
    Your analysis should be detailed, precise, and actionable, with specific price levels mentioned throughout.
    Focus on creating a clear roadmap for trading the London session today.
    """,
    expected_output="""
    A comprehensive analysis of today's EUR/USD London session trading bias with:
    1. Clear directional bias statement with confidence level
    2. Specific price levels for entry, stop, and targets
    3. Session-specific probabilities and scenarios
    4. Complete sequential trading framework
    5. Explicit references to the Daily Bias framework and Next Day model
    
    The analysis should be data-driven and immediately actionable for a London session trader.
    """,
    agent=session_analyst_agent,
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
    agent=report_writer_agent,
    async_execution=False
)
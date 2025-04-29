# tasks/market/weekly_report_tasks.py
from datetime import date, timedelta
from crewai import Task

from agents.market.economic_news_agent import economic_news_agent
from agents.market.fundamental_analyst_agent import fundamental_analyst_agent
from agents.market.technical_analyst_agent import technical_analyst_agent
from agents.market.sentiment_analyst_agent import sentiment_analyst_agent
from agents.market.report_writer_agent import report_writer_agent

# Calculate relevant dates
today_date = date.today()
past_week_start = (today_date - timedelta(days=7)).strftime("%Y-%m-%d")
today_date_str = today_date.strftime("%Y-%m-%d")
upcoming_week_end = (today_date + timedelta(days=7)).strftime("%Y-%m-%d")

# Define tasks
collect_fxstreet_news = Task(
    description=f"""
    Collect and analyze the latest EUR/USD news from FXStreet, focusing on high-impact red news events.
    
    Focus on:
    1. Major economic data releases for both EUR and USD
    2. ECB and Federal Reserve policy announcements and member speeches
    3. Market reaction to these events in the past week ({past_week_start} to {today_date_str})
    4. Upcoming high-impact events for next week ({today_date_str} to {upcoming_week_end})
    
    Create two separate sections in your analysis:
    
    SECTION 1: PAST WEEK REVIEW
    - Major economic events that impacted EUR/USD
    - Market reactions to these events
    - Surprises or deviations from expectations
    
    SECTION 2: UPCOMING EVENTS
    - Create a table of upcoming events with:
      * Date
      * Currency affected (EUR or USD)
      * Event name
      * Expected impact (High, Medium, Low) - focus on High impact (red) news
      * Previous reading and forecast if available
    
    Filter for the most important events that are likely to move EUR/USD significantly.
    Use FXStreet's categorization of "red" high-impact news as your primary filter.
    """,
    agent=economic_news_agent,
    expected_output="Comprehensive analysis of past and upcoming EUR/USD economic events from FXStreet, with special focus on high-impact red news."
)

analyze_technical_factors = Task(
    description=f"""
    Conduct a detailed technical analysis of EUR/USD focusing on:
    
    1. PRICE ACTION ANALYSIS
       - Recent price action from {past_week_start} to {today_date_str}
       - Major price levels that were tested/broken
       - Chart patterns (e.g., head and shoulders, double tops/bottoms, triangles)
       - Candlestick patterns (e.g., dojis, hammers, engulfing patterns)
    
    2. SUPPORT & RESISTANCE ANALYSIS
       - Identify key support levels with specific price points
       - Identify key resistance levels with specific price points
       - Note which levels are stronger based on historical tests/rejections
    
    3. INDICATOR ANALYSIS
       - Moving averages (50 MA, 100 MA, 200 MA) - positions and crossovers
       - RSI (Relative Strength Index) - overbought/oversold conditions, divergences
       - MACD - signal line crossovers, histogram trends
       - Bollinger Bands - squeezes, breakouts, trend direction
    
    4. TREND ANALYSIS
       - Current trend direction (bullish, bearish, or ranging)
       - Trend strength (strong, moderate, weak)
       - Potential trend reversal signals
    
    5. TECHNICAL OUTLOOK
       - Provide short-term (1-3 days) technical outlook
       - Provide medium-term (1-2 weeks) technical outlook
       - Identify key technical levels to watch
       - Technical-based price targets (both upside and downside scenarios)
    
    Your analysis should be detailed, precise, and actionable, with specific price levels mentioned throughout.
    Use technical analysis terminology correctly and explain your reasoning.
    """,
    agent=technical_analyst_agent,
    expected_output="Comprehensive 500-700 word technical analysis with precise support/resistance levels, indicator readings, and actionable outlook."
)

conduct_fundamental_analysis = Task(
    description=f"""
    Conduct a comprehensive fundamental analysis of EUR/USD, focusing on:
    
    1. MONETARY POLICY ANALYSIS
       - Current ECB monetary policy stance and recent changes
       - Current Federal Reserve monetary policy stance and recent changes
       - Interest rate differentials and expectations
       - Balance sheet policies and quantitative measures
       - Forward guidance from both central banks
    
    2. ECONOMIC DATA ANALYSIS
       - Comparative GDP growth between Eurozone and US
       - Inflation differentials and trends
       - Employment data comparison
       - Manufacturing and services sector performance
       - Consumer confidence and spending metrics
    
    3. GEOPOLITICAL FACTORS
       - Current geopolitical risks affecting the Euro
       - Current geopolitical risks affecting the US Dollar
       - Trade tensions or agreements
       - Political stability and election impacts (if relevant)
    
    4. FLOW ANALYSIS
       - Capital flows between Eurozone and US
       - Trade balance dynamics
       - Portfolio and investment flows
       - Central bank reserves and currency diversification
    
    5. FUNDAMENTAL OUTLOOK
       - Provide a short-term (1-2 weeks) fundamental outlook
       - Provide a medium-term (1-3 months) fundamental outlook
       - Identify key fundamental factors likely to drive EUR/USD
       - Potential fundamental-based price targets or ranges
    
    Your analysis should be detailed, data-driven, and focus on how these fundamental factors translate into potential currency movements.
    Use specific data points and statistics where relevant.
    """,
    agent=fundamental_analyst_agent,
    expected_output="Detailed 500-700 word fundamental analysis covering monetary policy, economic data, geopolitical factors, and data-driven outlook."
)

analyze_market_sentiment = Task(
    description=f"""
    Conduct a thorough sentiment analysis for EUR/USD currency pair, focusing on:
    
    1. POSITIONING DATA
       - CFTC Commitment of Traders (COT) data for EUR/USD
       - Changes in net positioning from institutional and speculative traders
       - Identify potential extreme positioning that could lead to reversals
    
    2. SOCIAL MEDIA SENTIMENT
       - Analyze sentiment on X (Twitter) from major forex accounts and hashtags
       - Monitor Reddit communities (r/Forex, r/Trading, etc.)
       - Track StockTwits and other retail trading platforms
       - Identify sentiment shifts and consensus views
    
    3. INSTITUTIONAL OUTLOOK
       - Summarize major bank forecasts for EUR/USD
       - Note recent changes in institutional outlook
       - Highlight consensus views and contrarian opinions
    
    4. RETAIL SENTIMENT
       - Analyze broker positioning ratios (percentage of clients long vs. short)
       - Identify changes in retail positioning
       - Look for extreme readings that might signal contrarian opportunities
    
    5. SENTIMENT INDICATORS
       - Fear & Greed indicators for forex markets
       - Put/Call ratios or similar derivatives sentiment metrics
       - Volatility expectations
    
    6. SENTIMENT OUTLOOK
       - Identify consensus view and potential contrarian opportunities
       - Note markets where sentiment appears stretched or vulnerable to reversal
       - Provide insights on how sentiment might influence price action
    
    Your analysis should be data-driven where possible, noting specific sentiment readings or percentages.
    Focus on how sentiment differs between retail and institutional traders, and where it might be providing trading opportunities.
    """,
    agent=sentiment_analyst_agent,
    expected_output="Detailed 400-600 word sentiment analysis covering positioning data, social media trends, and institutional vs. retail sentiment dynamics."
)

create_weekly_report = Task(
    description=f"""
    Compile a comprehensive professional EUR/USD weekly market report for the period {past_week_start} to {upcoming_week_end}.
    
    YOUR REPORT MUST INCLUDE THE FOLLOWING SECTIONS:
    
    1. TITLE: "EUR/USD Weekly Report – {today_date_str}"
    
    2. EXECUTIVE SUMMARY (150-200 words)
       - Brief overview of current EUR/USD status and key points
       - Major price movements from past week
       - Key drivers (summarize most important fundamental and technical factors)
       - Short outlook statement
    
    3. ECONOMIC EVENTS REVIEW AND FORECAST (400-500 words)
       - Summary of past week's major economic events and their impact
       - Table of upcoming economic events with dates, currency affected, and expected impact
       - Focus especially on high-impact "red" FXStreet events
    
    4. TECHNICAL ANALYSIS (500-700 words)
       - Price action analysis with specific price points
       - Support and resistance levels (with exact numbers)
       - Indicator readings and interpretation
       - Chart patterns and potential breakout/breakdown scenarios
       - Technical outlook with specific targets
    
    5. FUNDAMENTAL ANALYSIS (500-700 words)
       - Monetary policy comparison
       - Economic data analysis
       - Geopolitical factors
       - Flow analysis
       - Fundamental outlook with reasoning
    
    6. SENTIMENT ANALYSIS (400-500 words)
       - Positioning data and extremes
       - Social media sentiment trends
       - Institutional vs. retail outlook
       - Contrarian opportunities
    
    7. TRADING SCENARIOS (300-400 words)
       - Bullish scenario with entry points, targets, and stop levels
       - Bearish scenario with entry points, targets, and stop levels
       - Key risk events to watch
       - Risk management considerations
    
    8. CONCLUSION (150-200 words)
       - Summary of main points
       - Primary outlook for EUR/USD
       - Final thoughts and recommendation
    
    FORMATTING REQUIREMENTS:
    - Use proper Markdown formatting with headers, lists, tables
    - Make support/resistance levels and price targets stand out
    - Include section headers and sub-sections for readability
    - Ensure the report is well-structured and professional
    - Report should be comprehensive, approximately 2000-3000 words total
    
    IMPORTANT:
    - Be specific with price levels, dates, and targets
    - Provide actionable insights for traders
    - Ensure all analysis is data-driven and well-reasoned
    - This is a PROFESSIONAL report - avoid vague language and ensure all claims are substantiated
    - Make sure NOTHING is cut off or incomplete - the entire report must be delivered in full
    """,
    agent=report_writer_agent,
    expected_output="Complete, professional EUR/USD weekly market report in properly formatted Markdown, approximately 2000-3000 words with all sections fully completed."
)
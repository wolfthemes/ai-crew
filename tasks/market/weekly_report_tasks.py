# tasks/market/weekly_report_tasks.py
from datetime import date, datetime, timedelta
import pytz
from crewai import Task

# Import agents
from agents.market.economic_news_agent import economic_news_agent
from agents.market.fundamental_analyst_agent import fundamental_analyst_agent
from agents.market.technical_analyst_agent import technical_analyst_agent
from agents.market.sentiment_analyst_agent import sentiment_analyst_agent
from agents.market.weekly_report_writer_agent import weekly_report_writer_agent

# Calculate relevant dates
paris_tz = pytz.timezone('Europe/Paris')
paris_now = datetime.now(paris_tz)
today_date = paris_now.date()
today_str = today_date.strftime("%Y-%m-%d")
week_start = today_date - timedelta(days=today_date.weekday())
week_end = week_start + timedelta(days=6)
week_start_str = week_start.strftime("%Y-%m-%d")
week_end_str = week_end.strftime("%Y-%m-%d")

# Define tasks with explicit agent assignments
collect_fxstreet_news = Task(
    description=f"""
    Collect and analyze upcoming EUR/USD economic events from FXStreet for the week of {week_start_str} to {week_end_str}.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. HIGH-IMPACT EVENTS
       - All high-impact events for EUR and USD during the week
       - Expected market impact and analysis of potential outcomes
       - Previous readings and market reactions for similar events
       - Analysis of potential volatility around these events
    
    2. CENTRAL BANK FOCUS
       - Any ECB or Federal Reserve communications
       - Key speakers and their historical market impact
       - Policy expectations and potential surprises
       - Policy divergence analysis between ECB and Fed
    
    3. ECONOMIC DATA TRENDS
       - Compare current data releases to previous periods
       - Identify trends in economic indicators
       - Analyze surprise potential based on economist forecasts
       - Potential market reaction scenarios to different outcomes
    
    4. MARKET POSITIONING AHEAD OF EVENTS
       - How traders are likely positioned before key events
       - Potential for liquidity events around major releases
       - Risk scenarios for unexpected outcomes
    
    Use the get_fxstreet_events utility function to retrieve the current week's economic events.
    Your analysis should be comprehensive but focused on the most market-moving events.
    """,
    expected_output="""
    A detailed analysis of upcoming economic events for EUR/USD with:
    1. All high-impact events listed chronologically
    2. Central bank communications and implications
    3. Economic data trend analysis 
    4. Market positioning insights
    
    The analysis should be concise, specific, and actionable for trading decisions.
    """,
    agent=economic_news_agent,
    async_execution=False
)

analyze_technical_factors = Task(
    description=f"""
    Conduct a comprehensive technical analysis of EUR/USD across multiple timeframes for the week ahead.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. MULTIPLE TIMEFRAME ASSESSMENT
       - Monthly chart: long-term trend and major structural levels
       - Weekly chart: intermediate trend and key weekly levels
       - Daily chart: short-term trend and daily supply/demand zones
       - 4-hour chart: near-term market structure and potential trading setups
    
    2. KEY PRICE LEVELS
       - Major support and resistance zones
       - Previous week's high and low
       - Monthly/quarterly opens and closes
       - Psychological round numbers
       - Daily swing points and their significance
    
    3. MARKET STRUCTURE ANALYSIS
       - Higher timeframe market structure
       - Liquidity levels and potential liquidity engineering
       - Change in character analysis
       - Support/resistance flips and their implications
    
    4. TECHNICAL INDICATORS
       - Moving average relationships (20/50/200)
       - Relative Strength Index conditions
       - Potential divergences on multiple timeframes
       - Volatility indicators (ATR, Bollinger Bands)
    
    5. WEEKLY PATTERN PROJECTIONS
       - Classic Expansion potential
       - Consolidation Reversal scenarios
       - Midweek Reversal possibilities
       - Optimal day-of-week entry probabilities
    
    Your analysis should be detailed, precise, and actionable, with specific price levels mentioned throughout.
    Focus on creating a clear technical framework for the coming week's trading.
    """,
    expected_output="""
    A comprehensive technical analysis of EUR/USD with:
    1. Multiple timeframe assessment
    2. Specific price levels for support, resistance, and targets
    3. Detailed market structure analysis
    4. Technical indicator readings across timeframes
    5. Weekly pattern projections
    
    The analysis should provide a complete technical picture for the coming trading week.
    """,
    agent=technical_analyst_agent,
    async_execution=False
)

conduct_fundamental_analysis = Task(
    description=f"""
    Analyze the fundamental factors affecting EUR/USD for the week ahead, focusing on both short and medium-term drivers.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. MONETARY POLICY DIVERGENCE
       - ECB vs Fed policy stance comparison
       - Interest rate differential analysis
       - Quantitative tightening/easing programs
       - Forward guidance expectations
       - Policy meeting schedules and potential outcomes
    
    2. ECONOMIC GROWTH DYNAMICS
       - GDP growth comparison between Eurozone and US
       - Leading economic indicators differential
       - Recovery trajectories post-pandemic
       - Business sentiment in both regions
       - Consumer strength comparison
    
    3. INFLATION OUTLOOK
       - CPI/PCE trends in both economies
       - Core vs headline inflation divergence
       - Producer price developments
       - Wage growth pressures
       - Inflation expectations
    
    4. GEOPOLITICAL CONSIDERATIONS
       - Trade relationships
       - Energy dependency in Europe
       - Political stability factors
       - Regulatory developments
       - Global risk sentiment drivers
    
    5. FUNDAMENTAL BIAS PROJECTION
       - Short-term (1-2 weeks) fundamental bias
       - Medium-term (1-3 months) outlook
       - Potential fundamental shifts on the horizon
       - Key data to watch that could change the outlook
    
    Your analysis should be thorough but focused on factors most likely to drive EUR/USD price action.
    Include a clear fundamental bias statement with rationale.
    """,
    expected_output="""
    A comprehensive fundamental analysis of EUR/USD with:
    1. Detailed monetary policy divergence assessment
    2. Economic growth comparison between regions
    3. Inflation trajectory analysis for both economies
    4. Relevant geopolitical factors affecting the pair
    5. Clear fundamental bias projection with timeframes
    
    The analysis should be well-reasoned and directly tied to potential price movement.
    """,
    agent=fundamental_analyst_agent,
    async_execution=False
)

analyze_market_sentiment = Task(
    description=f"""
    Analyze the current market sentiment for EUR/USD, including positioning, sentiment indicators, and risk drivers.
    
    YOUR ANALYSIS MUST INCLUDE:
    
    1. POSITIONING DATA
       - COT (Commitment of Traders) report analysis
       - Large speculator net positioning
       - Commercial hedger activity
       - Retail sentiment indicators
       - Position adjustments over recent weeks
    
    2. RISK SENTIMENT ASSESSMENT
       - Risk-on/risk-off environment
       - Correlation with equity markets
       - Safe haven flows
       - Volatility regime analysis
       - Dollar strength/weakness context
    
    3. SENTIMENT INDICATORS
       - Put/call ratios relevant to FX markets
       - Economic surprise indices for EUR and USD
       - Consumer/business confidence comparisons
       - Institutional outlook surveys
       - Social media sentiment trends
    
    4. CONTRARIAN SIGNALS
       - Extreme positioning situations
       - Sentiment divergence from price
       - Potential capitulation signals
       - Complacency indicators
       - Consensus trade identification
    
    5. SENTIMENT BIAS PROJECTION
       - Short-term sentiment direction
       - Potential sentiment shifts on the horizon
       - Data releases that could change sentiment
       - Sentiment-driven price targets
       - Contrarian trade opportunities
    
    Your analysis should provide a clear picture of market sentiment and its potential impact on price.
    Include both quantitative and qualitative sentiment measures.
    """,
    expected_output="""
    A comprehensive market sentiment analysis for EUR/USD with:
    1. Detailed positioning data interpretation
    2. Current risk sentiment assessment
    3. Key sentiment indicator readings
    4. Potential contrarian signals
    5. Clear sentiment bias projection
    
    The analysis should connect sentiment factors directly to trading implications.
    """,
    agent=sentiment_analyst_agent,
    async_execution=False
)

create_weekly_report = Task(
    description=f"""
    Compile a comprehensive EUR/USD weekly market report for the week of {week_start_str} to {week_end_str}.
    
    YOUR REPORT MUST INCLUDE THE FOLLOWING SECTIONS:
    
    1. TITLE: "EUR/USD Weekly Report – {today_str}"
    
    2. EXECUTIVE SUMMARY (150-200 words)
       - Weekly bias statement (bullish/bearish/neutral) with confidence level
       - Key price levels to watch (support, resistance, targets)
       - Major news events for the coming week
       - Weekly trading strategy recommendation
    
    3. PREVIOUS WEEK RECAP (150-200 words)
       - Price action review of the previous week
       - Key levels that were tested
       - Important news events and market reactions
       - Weekly close assessment
    
    4. FUNDAMENTAL OUTLOOK (250-300 words)
       - Monetary policy comparison (ECB vs Fed)
       - Economic growth dynamics
       - Inflation outlook for both economies
       - Geopolitical factors affecting EUR/USD
       - Fundamental bias statement with rationale
    
    5. TECHNICAL ANALYSIS (300-350 words)
       - Multiple timeframe assessment
       - Key support and resistance zones
       - Market structure analysis
       - Technical indicator readings
       - Weekly pattern identification (Classic Expansion, Consolidation Reversal, or Midweek Reversal)
    
    6. MARKET SENTIMENT (200-250 words)
       - Positioning data analysis
       - Risk sentiment assessment
       - Sentiment indicators review
       - Contrarian signals
       - Sentiment bias projection
    
    7. ECONOMIC CALENDAR (150-200 words)
       - Table of key economic events for the week
       - Impact assessment for each major release
       - Volatility expectations around events
       - Watch points for potential surprises
    
    8. WEEKLY TRADING PLAN (200-250 words)
       - Day-by-day approach for the week
       - Key levels for entries and exits
       - Risk management parameters
       - Session-specific opportunities (London, NY)
       - Contingency scenarios
    
    FORMATTING REQUIREMENTS:
    - Use proper Markdown formatting with headers, lists, tables
    - Make key levels and price targets stand out (bold)
    - Include section headers and sub-sections for readability
    - Ensure the report is well-structured and professional
    - Report should be comprehensive, approximately 1400-1750 words total
    
    IMPORTANT:
    - Be specific with price levels, times, and targets
    - Provide both weekly context and day-specific insights
    - Ensure all analysis is data-driven and well-reasoned
    - This is a PROFESSIONAL report - avoid vague language and ensure all claims are substantiated
    - Focus on actionable insights that can be implemented in a trading plan
    """,
    expected_output="""
    Complete, professional EUR/USD weekly market report in properly formatted Markdown,
    approximately 1400-1750 words with all sections fully completed.
    
    The report should provide clear, actionable trading guidance for the coming week,
    with specific levels, strategies, and a day-by-day approach.
    """,
    agent=weekly_report_writer_agent,
    async_execution=False
)
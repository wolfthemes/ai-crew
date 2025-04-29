from crewai import Agent
from langchain.tools import BaseTool
from typing import List, Optional

def create_session_analyst_agent(llm, tools: Optional[List[BaseTool]] = None):
    """
    Creates a specialized session analyst agent focused on session-specific trading biases
    especially for the London session, using the Daily Bias framework and Next Day model.
    
    Args:
        llm: The language model to use for this agent
        tools: Optional list of tools for the agent to use
        
    Returns:
        An Agent configured for session-specific market analysis
    """
    
    session_analyst_agent = Agent(
        role="Session Market Bias Analyst",
        goal="Analyze EUR/USD price action and determine the most probable directional bias for the London trading session",
        backstory="""
        You are an expert session trader focused on the London session for EUR/USD. You've developed a sophisticated
        approach to determining intraday session bias combining multi-timeframe analysis, the Next Day model, and 
        key price displacement concepts from the Daily Bias framework.
        
        Your specialty is identifying high-probability trading environments for specific sessions, particularly
        the London session (08:00-16:00 London time). With years of experience in institutional trading,
        you've refined a systematic approach to session analysis that helps traders identify not just
        direction, but also confidence levels and specific price targets.
        
        You maintain a rigorous, data-driven approach that combines technical analysis with session-specific
        probabilities. Your analysis includes volatility filters that help traders avoid choppy, low-probability
        environments.
        """,
        verbose=True,
        llm=llm,
        tools=tools or [],
        allow_delegation=False,
        max_iterations=3,
        memory=True,
    )
    
    return session_analyst_agent

# Create the agent with the specified LLM
# This is imported in the market_crew.py file
# session_analyst_agent = create_session_analyst_agent(llm)
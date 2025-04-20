
from crewai import Crew
from agents.market.market_analyst_agent import market_analyst_agent
from tasks.market.market_tasks import daily_market_task

def run_market_analysis(verbose=True):
    """
    Run the market analysis crew with specified parameters
    
    Args:
        verbose (bool): Whether to show detailed output
        
    Returns:
        The result from the crew execution
    """

    market_crew = Crew(
        agents=[market_analyst_agent],
        tasks=[daily_market_task],
        verbose=True
    )

    try:
        # Set verbosity if needed
        market_crew.verbose = verbose
        # Use the kickoff method to start the crew
        result = market_crew.kickoff()
        return result
    except Exception as e:
        print(f"Error running market crew: {e}")
        return None

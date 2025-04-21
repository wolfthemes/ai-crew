
from crewai import Crew, Process
from agents.market.market_analyst_agent import market_analyst_agent
from agents.market.economic_news_agent import economic_news_agent
from agents.market.fundamental_analyst_agent import fundamental_analyst_agent
from agents.market.report_writer_agent import report_writer_agent
from tasks.market.market_tasks import collect_economic_news, conduct_funamental_analysis_of_eurusd, create_report

from tasks.market.market_tasks import daily_market_task

def run_market_analysis(verbose=True):
    """
    Run the market analysis crew with specified parameters
    
    Args:
        verbose (bool): Whether to show detailed output
        
    Returns:
        The result from the crew execution
    """

    # market_crew = Crew(
    #     agents=[market_analyst_agent],
    #     tasks=[daily_market_task],
    #     verbose=True
    # )

    market_crew = Crew(
        agents=[economic_news_agent, fundamental_analyst_agent, report_writer_agent],
        tasks=[collect_economic_news, conduct_funamental_analysis_of_eurusd, create_report],
        process=Process.sequential,  # Tasks executed in order, with outputs passed to report writer
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

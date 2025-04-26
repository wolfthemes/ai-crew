from crewai import Crew, Process
from agents.support.research_agent import research_agent
from agents.support.support_agent import support_agent
from agents.support.quality_agent import support_quality_control_agent

from utils.ticket_utils import get_ticket_metadata
from tasks.support.research_task import create_research_task
from tasks.support.support_tasks import create_support_reply_task
from tasks.support.quality_tasks import review_support_reply_task

def support_crew_with_research(ticket_text: str, instruction: str = "", ticket_id: str = ""):
    """
    Crew pipeline: Research → Support Reply → Review
    Now passing instructions to research agent as well
    """

    if ticket_id:
        ticket_meta = get_ticket_metadata(ticket_id)
    else:
        ticket_meta = {}

    # 1. Research the ticket and structure its issues
    # Now passing instruction to research task
    research_task = create_research_task(
        ticket_text, 
        instruction=instruction, 
        ticket_meta=ticket_meta
    )
    research_task.name = "Research"
    research_data = research_task._output["research_output"]
    
    #print( ticket_meta )
    #print( research_data )
    #print( instruction )

    # 2. Generate the support reply using research result
    support_task = create_support_reply_task(
        ticket_text, 
        research_data, 
        instruction=instruction, 
        ticket_meta=ticket_meta
    )
    support_task.name = "Support Reply"
    support_task.context = [research_task]

    # 3. Review the reply
    review_task = review_support_reply_task(
        ticket_text, 
        instruction=instruction, 
        ticket_meta=ticket_meta
    )
    review_task.name = "Review"
    review_task.context = [support_task]

    crew = Crew(
        agents=[research_agent, support_agent, support_quality_control_agent],
        tasks=[research_task, support_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()

    return {
        "research": research_task.output,
        "reply": support_task.output,
        "review": review_task.output
    }

# Legacy
def support_crew_fresh_with_review(ticket_text, instruction: str = ""):
    """
    Creates a crew that generates a support reply and then reviews it,
    without creating an infinite loop.
    
    Now includes instruction parameter to pass to both agents
    """
    # Create the support reply task with instruction
    support_task = create_support_reply_task(ticket_text, instruction=instruction)
    support_task.name = "Support Reply"
    
    # Create the quality review task with instruction
    quality_task = review_support_reply_task(ticket_text, instruction=instruction)
    quality_task.name = "Quality Review"
    
    # Set up the task dependency
    quality_task.context = [support_task]
    
    # Create the crew with a sequential process to prevent looping
    crew = Crew(
        agents=[support_agent, support_quality_control_agent],
        tasks=[support_task, quality_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute the crew
    crew.kickoff()

    # Access results by task_id
    return {
        "reply": support_task.output,
        "review": quality_task.output
    }
from crewai import Crew, Process
from agents.support_agent import support_agent
from agents.support_quality_control_agent import support_quality_control_agent
from tasks.support_tasks import create_support_reply_task
from tasks.quality_tasks import review_support_reply_task

def support_crew_fresh_with_review(ticket_text, kb_result):
    """
    Creates a crew that generates a support reply and then reviews it,
    without creating an infinite loop.
    
    Returns a dictionary with both the reply and the review.
    """
    # Create the support reply task
    support_task = create_support_reply_task(ticket_text, kb_result)
    
    # Create the quality review task with a clear dependency on the support task
    quality_task = review_support_reply_task(ticket_text, kb_result)
    
    # Create the crew with a sequential process to prevent looping
    crew = Crew(
        agents=[support_agent, support_quality_control_agent],
        tasks=[support_task, quality_task],
        process=Process.sequential,  # Ensure sequential execution
        verbose=True
    )
    
    # Execute the crew
    result = crew.kickoff()
    
    # Parse results
    # The first task result is the support reply, the second is the quality review
    return {
        "reply": result[0],  # Support reply
        "review": result[1]  # Quality review
    }
from crewai import Crew, Process
from agents.support_agent import support_agent
from agents.support_quality_control_agent import support_quality_control_agent
from tasks.support_tasks import create_support_reply_task
from tasks.quality_tasks import review_support_reply_task

def support_crew_fresh_with_review(ticket_text):
    """
    Creates a crew that generates a support reply and then reviews it,
    without creating an infinite loop.
    
    Returns a dictionary with both the reply and the review.
    """
    # Create the support reply task with a specific task ID
    support_task = create_support_reply_task(ticket_text)
    support_task.name = "Support Reply"
    
    # Create the quality review task with a clear dependency on the support task
    quality_task = review_support_reply_task(ticket_text)
    quality_task.name = "Quality Review"
    
    # Set up the task dependency - quality reviews the support reply
    quality_task.context = [support_task]
    
    # Create the crew with a sequential process to prevent looping
    crew = Crew(
        agents=[support_agent, support_quality_control_agent],
        tasks=[support_task, quality_task],
        process=Process.sequential,  # Ensure sequential execution
        verbose=True
    )
    
    # Execute the crew
    crew.kickoff()

    # Access results by task_id
    return {
        "reply": support_task.output,
        "review": quality_task.output
    }
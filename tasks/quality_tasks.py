from crewai import Task
from agents.support_quality_control_agent import support_quality_control_agent
from utils.document_loaders import load_guidelines

def review_support_reply_task(ticket_text, kb_result):
    """
    Creates a task for the quality control agent to review a support reply,
    with proper context to prevent looping back
    """
    guidelines = load_guidelines()
    
    return Task(
        description=f"""
        Review the support agent's reply to this ticket.
        
        ### Original Ticket:
        {ticket_text}
        
        ### Knowledge Base Source:
        Source: {kb_result['source']}
        Title: {kb_result['title']}
        
        ### Guidelines:
        {guidelines}
        
        IMPORTANT: Your job is to review the support reply from the previous task.
        DO NOT create a new reply - only evaluate the existing one.
        
        Check if the reply:
        1. Follows our support guidelines
        2. Uses the knowledge base information correctly
        3. Is helpful and accurate
        4. Has the right tone and format
        """,
        expected_output="Quality assessment report with specific feedback on the support reply.",
        agent=support_quality_control_agent,
        context=[],  # This will be filled by the crew with the output of the previous task
    )
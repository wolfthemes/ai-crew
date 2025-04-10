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
        Review the support agent's reply to this ticket:

        ### Original Ticket:
        {ticket_text}

        ### Knowledge Base Source:
        {kb_result}

        ### Guidelines:
        {guidelines}

        Review ONLY the previous agent's response against our guidelines.
        Do NOT create a new reply - only evaluate the existing one.
        """,
        expected_output="Quality assessment report with specific feedback on the support reply.",
        agent=support_quality_control_agent,
        context=[
            # This context will contain the output from the support task
            # The CrewAI framework will automatically pass the support reply here
        ],
        output_file="quality_review.md"  # Optional: save the output to a file
    )
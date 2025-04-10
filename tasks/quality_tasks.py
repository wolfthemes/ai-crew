from crewai import Task
from agents.support_quality_control_agent import support_quality_control_agent
from utils.document_loaders import load_guidelines

def review_support_reply_task(ticket_text, kb_result):
    """
    Creates a task for the quality control agent to review a support reply,
    with proper context to prevent looping back
    """
    guidelines = load_guidelines()

    parts = split_ticket_into_parts(ticket_text)
    classified_parts = [(p, classify_ticket(p)) for p in parts]
    issue_summary = "\\n".join([f"- {cat}: \"{part}\"" for part, cat in classified_parts])

    source_info = f"Source: {kb_result['source'] if kb_result and 'source' in kb_result else 'N/A'}"
    source_title = f"Source: {kb_result['title'] if kb_result and 'title' in kb_result else 'N/A'}"
    
    return Task(
        description=f"""
        Review the support agent's reply to this ticket.
        
        ### Original Ticket:
        {ticket_text}
        
        ### Knowledge Base Source:
        Source: {source_info}
        Title: {source_title}
        
        ### Guidelines:
        {guidelines}

        Internally, this ticket contains the following parts:
        {issue_summary}
        
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
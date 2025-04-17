from crewai import Task
from agents.quality_agent import support_quality_control_agent
from utils.document_loaders import load_guidelines

def review_support_reply_task(ticket_text: str, instruction: str = "", ticket_meta: dict = None) -> Task:
    guidelines = load_guidelines()

    return Task(
        description=f"""
        Review the support agent's reply to this ticket.

        ### Original Ticket:
        {ticket_text}

        Guidelines:
        {guidelines}

        Optional additional instruction from human operator:
        {instruction}

        IMPORTANT: Your job is to review the support reply from the previous task.
        DO NOT create a new reply - only evaluate the existing one.

        Check if the reply:
        1. Follows our support guidelines
        2. Uses the knowledge base information correctly
        3. Uses the additional instruction if provided
        4. Is helpful and accurate
        5. Has the right tone and format
        6. Is formatted in HTML and NOT in markdown or plain text
        """,
        expected_output="Quality assessment report with specific feedback on the support reply.",
        agent=support_quality_control_agent
    )

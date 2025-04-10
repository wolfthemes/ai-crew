from crewai import Task
from agents.support_agent import support_agent
from utils.document_loaders import load_guidelines

def create_support_reply_task(ticket_text, kb_result):
    """
    Creates a task for the support agent to respond to a ticket,
    using pre-fetched knowledge base results
    """
    guidelines = load_guidelines()
    
    return Task(
        description=f"""
        You are responding to this customer support ticket:

        {ticket_text}

        {guidelines}

        Here are the most relevant knowledge base results:
        {kb_result}

        Create a helpful and accurate response based on these results.
        """,
        expected_output="Markdown formatted support reply that directly addresses the customer's issue.",
        agent=support_agent,
        output_file="support_reply.md"  # Optional: save the output to a file
    )
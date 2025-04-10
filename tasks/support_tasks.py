from crewai import Task
from agents.support_agent import support_agent
from utils.ticket_classifier import classify_ticket, split_ticket_into_parts
from utils.document_loaders import load_guidelines

def create_support_reply_task(ticket_text, kb_result):
    """
    Creates a task for the support agent to respond to a ticket,
    using pre-fetched knowledge base results
    """
    guidelines = load_guidelines()

    parts = split_ticket_into_parts(ticket_text)
    classified_parts = [(p, classify_ticket(p)) for p in parts]
    issue_summary = "\\n".join([f"- {cat}: \"{part}\"" for part, cat in classified_parts])

    source_info = f"Source: {kb_result['source'] if kb_result and 'source' in kb_result else 'N/A'}"
    source_title = f"Title: {kb_result['title'] if kb_result and 'title' in kb_result else 'N/A'}"
    source_content = f"Content: {kb_result['content'] if kb_result and 'content' in kb_result else 'N/A'}"
    
    # Check if we have a strict response
    strict_instruction = ""
    if kb_result and kb_result.get("is_strict", False) and "STRICT_RESPONSE:" in kb_result.get("content", ""):
        strict_instruction = """
        IMPORTANT: This is a common issue with a predefined response.
        You MUST use the exact predefined response provided below, without modification.
        """
    
    return Task(
        description=f"""
        You are responding to this customer support ticket:

        {ticket_text}

        {guidelines}

        Internally, this ticket contains the following parts:
        {issue_summary}

        Here are the most relevant knowledge base results:
        Source: {source_info}
        Title: {source_title}
        Content: {source_content}

        {strict_instruction}

        Create a helpful and accurate response based on these results.
        """,
        expected_output="Markdown formatted support reply that directly addresses the customer's issue.",
        agent=support_agent
    )
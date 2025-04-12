from crewai import Task
from agents.support_agent import support_agent
from utils.ticket_classifier import classify_ticket, split_ticket_into_parts
from utils.document_loaders import load_guidelines

def create_support_reply_task(ticket_text: str, research_output: str = None, instruction: str = "") -> Task:
    guidelines = load_guidelines()

    return Task(
        description=f"""
        You are a support expert. Your job is to respond to this customer support ticket:
        {ticket_text}

        Guidelines:
        {guidelines}

        Optional additional instruction from human operator:
        {instruction}

        You are provided with pre-processed research output below.
        Each ticket part has been matched against the KB.
        If a match starts with "STRICT_RESPONSE:", this means you must use the exact response content as-is — without rewording or paraphrasing it. 
        However, do NOT include the label "STRICT_RESPONSE:" in the final reply. Just use the response body as part of your answer.

        === RESEARCH OUTPUT ===
        {research_output}

        Use ONLY this data to generate your response.
        - If no match is found, explain clearly and politely.
        """,
        expected_output = "Support reply formatted in clean HTML, ready for copy-paste into Ticksy.",
        agent=support_agent
    )

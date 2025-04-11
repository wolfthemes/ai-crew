from crewai import Task
from agents.support_agent import support_agent
from utils.ticket_classifier import classify_ticket, split_ticket_into_parts
from utils.document_loaders import load_guidelines

def create_support_reply_task(ticket_text: str, research_output: str = None) -> Task:
    guidelines = load_guidelines()

    return Task(
        description=f"""
        You are a support expert. Your job is to respond to this customer support ticket:

        {ticket_text}

        Guidelines:
        {guidelines}

        You are provided with pre-processed research output below.
        Each ticket part has been matched against the KB.
        If a part includes a match starting with "STRICT_RESPONSE:", you MUST use it as-is — without modifying it.

        === RESEARCH OUTPUT ===
        {research_output}

        Use ONLY this data to generate your response.
        - If STRICT_RESPONSE is present, do not change or paraphrase it.
        - If no match is found, explain clearly and politely.
        """,
        expected_output="Markdown-formatted support reply.",
        agent=support_agent
    )
from crewai import Task
from agents.support_quality_control_agent import support_quality_control_agent
from utils.document_loaders import load_guidelines

def review_support_reply_task(ticket_text: str) -> Task:
    guidelines = load_guidelines()

    return Task(
        description="Review the support agent's reply using the provided source and guidelines.",
        expected_output="Quality assessment report with specific feedback on the support reply.",
        agent=support_quality_control_agent,
        context=[],  # This will still receive the support reply task
        tool_args={
            "reply": lambda ctx: ctx[0].output.raw,  # reply content from previous task
            "ticket": ticket_text,
            "source_doc": lambda ctx: ctx[0].metadata.get("source_doc", ""),  # customize if you store this
            "guidelines": guidelines
        }
    )

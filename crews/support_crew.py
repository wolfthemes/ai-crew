from crewai import Crew
from tasks.task_fresh_ticket import support_task_fresh
from tasks.task_ticket_followup import support_task_conversation
from tasks.task_review_support_reply import build_review_task
from agents.support_agent import support_agent
from agents.support_quality_control_agent import support_quality_control_agent

def support_crew_fresh_with_review(ticket_text, kb_result):
    # Inject KB + ticket into the support agent task
    support_task_fresh.description = f"""
You are replying to this customer ticket:

{ticket_text}

Use this knowledge base result:
{kb_result}

Be brief, use markdown formatting, and only say what the KB recommends.
"""

    # Run support agent task
    support_crew = Crew(
        agents=[support_agent],
        tasks=[support_task_fresh],
        verbose=False
    )
    support_reply = support_crew.kickoff()

    # Build and run review task
    review_task = build_review_task(ticket_text, kb_result, support_reply)
    review_crew = Crew(
        agents=[support_quality_control_agent],
        tasks=[review_task],
        verbose=False
    )
    review_result = review_crew.kickoff()

    return {
        "reply": support_reply,
        "review": review_result
    }

support_crew_fresh = Crew(
    agents=[support_agent],
    tasks=[support_task_fresh],
    verbose=True
)

support_crew_conversation = Crew(
    agents=[support_agent],
    tasks=[support_task_conversation],
    verbose=True
)
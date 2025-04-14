from crewai import Task
from agents.support_quality_control_agent import support_quality_control_agent

def build_review_task(ticket_text, kb_result, support_reply):
    return Task(
        description=f"""
You are reviewing a support reply for quality control.

### Ticket:
{ticket_text}

### Support Agent Reply:
{support_reply}

### KB Match Used:
{kb_result}

You must verify:
- ✅ That the reply reuses the KB content faithfully (especially if from `common_issues`)
- ❌ That no hallucinated or generic web advice is present
- ✅ That the tone is warm, professional, markdown-formatted
- ✅ That it ends with a proper sign-off ("I hope it helps", "Best regards", etc.)

If the reply is perfect, respond with **'Approved ✅'**
Otherwise, list required changes in bullet points.
        """,
        expected_output="Review result: either 'Approved ✅' or a bullet list of issues",
        agent=support_quality_control_agent
    )


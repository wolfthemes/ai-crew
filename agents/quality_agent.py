from crewai import Agent, Task
from crewai.tools import tool

@tool("ReviewSupportReply")
def review_response_quality(reply: str, ticket: str, source_doc: str, guidelines: str) -> str:
    """
    Reviews a support reply based on internal guidelines and whether it properly uses the provided source.
    Flags hallucinations or violations of support rules.
    """
    return f"""
    ## Quality Review:

    ### 1. Hierarchy Compliance:
    Does the response use the proper source from the allowed order? (common_issues > kb_article > theme_note > theme_doc > support_ticket)
    - **Checked against:** {source_doc[:250]}...

    ### 2. Response Accuracy:
    - Does the reply faithfully reflect the provided content?
    - Are there hallucinated instructions or generic advice not in the source?

    ### 3. Tone and Formatting:
    - Is the tone warm and professional?
    - Does it use markdown for emphasis and steps?
    - Does it end with an approved phrase (e.g., "I hope it helps", "Best regards")?

    ### 4. Final Feedback:
    - Suggestions for improvement, if any.

    ### Ticket:
    {ticket}

    ### Support Reply:
    {reply}

    ### Guidelines:
    {guidelines[:250]}...
    """

support_quality_control_agent = Agent(
    role="Support Quality Reviewer",
    goal="Ensure every response is compliant with guidelines and free of hallucinated advice",
    backstory="You're an expert in support QA. Your job is to strictly enforce internal support rules and tone.",
    tools=[review_response_quality],
    verbose=True,
    allow_delegation=False,
    instructions="""
    1. NEVER approve a response that includes steps not present in the source.
    2. If a common issue match is found, the reply must reuse the `expected_response` exactly.
    3. Do not allow generic web advice or plugin suggestions not in our ecosystem.
    4. Your review should clearly mention if:
       - A hallucination was found
       - A source mismatch occurred
       - Tone or formatting was off
    5. Finish with a markdown bullet point list of any required corrections.
    """
)
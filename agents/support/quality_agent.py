from crewai import Agent
from crewai.tools import tool
from tools.vector_retriever import support_agent_backstory_text, support_agent_instructions_text
from core.llm_config import get_llm

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
    - Does it uses 'I' and not 'we'
    - Does it end with an approved phrase (e.g., "I hope it helps", "Best regards")?
    - Verify that the reply tone matches the examples from previous closed tickets (professional, warm, concise).
    - Verify that the reply is formatted in HTML

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
    llm=get_llm("primary"),
    instructions="""
    - NEVER approve a response that includes steps not present in the source.
    - If a common issue match is found, the reply must reuse the `expected_response` exactly.
    - Do not allow generic web advice or plugin suggestions not in our ecosystem.
    - If the support agent reply includes advice or information that does NOT come from the matched source or goes beyond the scope of the ticket, FLAG IT AS HALLUCINATION and mark the reply as needing revision.
    - Your review should clearly mention if:
      - A hallucination was found
      - A source mismatch occurred
      - Tone or formatting was off
    - Finish with a markdown bullet point list of any required corrections.

    Use the ReviewSupportReply tool to evaluate the support reply. Do not try to reason about quality by yourself.

    Do not use stringified JSON — call the tool with named arguments.
    """
)

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class ReviewReplyInput(BaseModel):
    reply: str = Field(..., description="The support reply to review")
    ticket: str = Field(..., description="The original customer ticket")
    source_doc: str = Field(..., description="The KB result or STRICT_RESPONSE used")
    guidelines: str = Field(..., description="Internal tone, style and accuracy rules")

class ReviewSupportReplyTool(BaseTool):
    name: str = "ReviewSupportReply"
    description: str =  """
    Reviews a support reply based on internal guidelines and whether it properly uses the provided source.
    Flags hallucinations or violations of support rules.
    """
    args_schema: Type[BaseModel] = ReviewReplyInput

    def _run(self, reply: str, ticket: str, source_doc: str, guidelines: str) -> str:
        
        return f"""
    ## Quality Review:

    ### 1. Hierarchy Compliance:
    Does the response use the proper source from the allowed order? (common_issues > kb_article > theme_doc > support_ticket)
    - **Checked against:** {source_doc[:250]}...

    ### 2. Response Accuracy:
    - Does the reply faithfully reflect the provided content?
    - Are there hallucinated instructions or generic advice not in the source?

    ### 3. Tone and Formatting:
    - Does it avoid reformulating the issue?
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
    def run(self, query: str) -> str:
        return self._run(query)
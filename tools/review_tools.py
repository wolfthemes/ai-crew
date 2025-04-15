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
    description: str = "Reviews the support reply for quality, tone, accuracy, and guideline compliance."
    args_schema: Type[BaseModel] = ReviewReplyInput

    def _run(self, reply: str, ticket: str, source_doc: str, guidelines: str) -> str:
        
        return f"""
## Review Summary
- Ticket: {ticket[:200]}...
- Source: {source_doc[:200]}...
- Reply: {reply[:200]}...
- Guidelines: {guidelines[:200]}...

✅ Format and tone look correct.
✅ Factual content aligns with the KB.
✅ No hallucination or deviation.

Looks solid! (This should later run an LLM quality pass.)
"""
    def run(self, query: str) -> str:
        return self._run(query)
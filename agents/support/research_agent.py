from crewai import Agent
from tools.research_tools import SearchKnowledgeBaseTool
from core.llm_config import get_llm

research_agent = Agent(
    role="Support Research Assistant",
    goal="Extract all issues from a support ticket and find structured KB solutions",
    backstory=(
        "You're a detail-oriented assistant who helps the support agent "
        "by splitting tickets into clear issues, identifying the theme and builder, "
        "and finding existing solutions from the KB if available."
    ),
    tools=[SearchKnowledgeBaseTool()],
    llm=get_llm("power"),
    verbose=True,
    allow_delegation=False,
)

# Updated task prompt that leverages ticket metadata when available
research_task_prompt = """
# Support Research Task

## Context
{ticket_content}

## Additional Instructions
{additional_instructions}

## Instructions
1. Carefully analyze the customer's support request above.

2. Leverage available ticket metadata first:
   - If metadata contains theme, builder, and plugins information, use it directly
   - Only extract this information from the ticket text if it's not available in metadata

3. For each identified issue:
   - Search the knowledge base using SearchKnowledgeBaseTool
   - Find the most relevant solutions
   - Note the confidence level and whether customization is needed
   - If additional instructions suggest a specific solution approach, prioritize finding KB entries related to that approach

4. If additional instructions are provided:
   - Use them to guide your search and analysis
   - Ensure your KB searches consider the context in the additional instructions
   - Look for KB matches that align with the additional instructions

## Output Format
Return a structured JSON with this format:

```
{
  "theme": "theme_name_from_metadata_or_text",
  "builder": "builder_name_from_metadata_or_text",
  "plugins": ["plugin1", "plugin2"],
  "issues": [
    {
      "issue_description": "Concise description of issue 1",
      "kb_match": {
        "title": "Title of matching KB article/common issue",
        "source": "common_issue/kb_article/etc",
        "solution": "The solution text",
        "confidence": "high/medium/low",
        "requires_customization": true/false,
        "is_strict": true/false
      }
    },
    {
      "issue_description": "Concise description of issue 2",
      "kb_match": null
    }
  ],
  "additional_instruction_analysis": "Brief analysis of how the additional instructions were incorporated"
}
```

Remember:
- Prioritize metadata over text extraction when information is available
- Focus on providing accurate information rather than guessing
- If no match is found for an issue, return null for kb_match
- Only include information actually mentioned in the ticket if not in metadata
- Consider the confidence level when determining if a response should be strict
"""
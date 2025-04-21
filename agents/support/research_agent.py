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

# Updated task prompt with properly formatted JSON example
research_task_prompt = """
# Support Research Task

## Context
{ticket_content}

## Additional Instructions
{additional_instructions}

## Instructions
1. Carefully analyze the customer's support request above.
2. Extract the following key information:
   - Theme name: Identify which WordPress theme they're using (if mentioned)
   - Page builder: Identify if they're using Elementor, WPBakery, etc. (if mentioned)
   - Plugins: List any plugins mentioned in the request
   - Main issues: Break down complex requests into individual issues

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
{{
  "theme": "theme_name_or_empty_if_unknown",
  "builder": "builder_name_or_empty_if_unknown",
  "plugins": ["plugin1", "plugin2"],
  "issues": [
    {{
      "issue_description": "Concise description of issue 1",
      "kb_match": {{
        "title": "Title of matching KB article/common issue",
        "source": "common_issue/kb_article/etc",
        "solution": "The solution text",
        "confidence": "high/medium/low",
        "requires_customization": true/false,
        "is_strict": true/false
      }}
    }},
    {{
      "issue_description": "Concise description of issue 2",
      "kb_match": null
    }}
  ],
  "additional_instruction_analysis": "Brief analysis of how the additional instructions were incorporated"
}}
```

Remember:
- Focus on providing accurate information rather than guessing
- If no match is found for an issue, return null for kb_match
- Only include information actually mentioned in the ticket
- Consider the confidence level when determining if a response should be strict
"""
from crewai import Agent
from tools.kb_tools import search_kb_structured  # or search_kb_structured if renamed

research_agent = Agent(
    role="Support Research Assistant",
    goal="Extract all issues from a support ticket and find structured KB solutions",
    backstory=(
        "You're a detail-oriented assistant who helps the support agent "
        "by splitting tickets into clear issues, identifying the theme and builder, "
        "and finding existing solutions from the KB if available."
    ),
    tools=[],  # We may not need tools if it works directly with core
    verbose=True,
)

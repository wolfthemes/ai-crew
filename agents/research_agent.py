from crewai import Agent
from tools.crewai_tools import SearchKnowledgeBaseTool, GetThemeBuilderTool

research_agent = Agent(
    role="Support Research Assistant",
    goal="Extract all issues from a support ticket and find structured KB solutions",
    backstory=(
        "You're a detail-oriented assistant who helps the support agent "
        "by splitting tickets into clear issues, identifying the theme and builder, "
        "and finding existing solutions from the KB if available."
    ),
    tools=[SearchKnowledgeBaseTool(),GetThemeBuilderTool()],
    verbose=True,
)

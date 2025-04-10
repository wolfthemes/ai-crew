from crews.support_crew import support_crew_fresh_with_review
from agents.support_agent import search_kb_raw

ticket_text = "How to update WPBakery to 8.3.1?"

# 1. Use KB tool
kb_result = search_kb_raw(ticket_text)

# 2. Run both reply and review
result = support_crew_fresh_with_review(ticket_text, kb_result)

print("📝 Support Reply:\n")
print(result["reply"])

print("\n🔎 Quality Review:\n")
print(result["review"])

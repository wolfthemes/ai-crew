from crews.support_crew import support_crew_fresh_with_review
from agents.support_agent import search_kb_raw
from utils.ticket_classifier import classify_ticket

def main():
    ticket_text = "How to update WPBakery to 8.3.1?"
    
    # 1. Classify the ticket for internal use
    category = classify_ticket(ticket_text)
    print(f"📋 Ticket classified as: {category}")
    
    # 2. Use KB tool to get relevant information
    kb_result = search_kb_raw(ticket_text)
    print(f"📚 Knowledge base searched.")
    
    # 3. Run both reply and review with proper crew
    print("🤖 Starting support crew...")
    result = support_crew_fresh_with_review(ticket_text, kb_result)
    
    print("\n📝 Support Reply:\n")
    print(result["reply"])
    
    print("\n🔎 Quality Review:\n")
    print(result["review"])

if __name__ == "__main__":
    main()
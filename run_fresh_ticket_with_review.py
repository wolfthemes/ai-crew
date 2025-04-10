from crews.support_crew import support_crew_fresh_with_review
from utils.ticket_classifier import classify_ticket
from agents.support_agent import search_kb_raw

def main():
    ticket_text = """
Ticket from user:

"How to update WPBakery with Herion?
John"
"""
    
    # 1. Classify the ticket for internal use
    category = classify_ticket(ticket_text)
    print(f"📋 Ticket classified as: {category}")
    
    # 2. Use KB tool to get relevant information
    kb_result = search_kb_raw(ticket_text)
    print(f"📚 Knowledge base searched.")
    
    # 3. Run both reply and review with proper crew
    print("🤖 Starting support crew...")
    try:
        result = support_crew_fresh_with_review(ticket_text, kb_result)
        
        print("\n📝 Support Reply:\n")
        print(result["reply"])
        
        print("\n🔎 Quality Review:\n")
        print(result["review"])
    except Exception as e:
        print(f"\n❌ Error running crew: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
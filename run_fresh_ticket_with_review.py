from crews.support_crew import support_crew_fresh_with_review
from utils.ticket_classifier import classify_ticket

def main():
    ticket_text = """
Ticket from user:

"How to update WPBakery with Herion?
John"
"""

    # 1. Classify the ticket
    category = classify_ticket(ticket_text)
    print(f"📋 Ticket classified as: {category}")

    # 2. Run the crew — let the agents/tools handle the rest
    print("🤖 Starting support crew...")

    try:
        result = support_crew_fresh_with_review(ticket_text)

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

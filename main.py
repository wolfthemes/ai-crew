from dotenv import load_dotenv
import sys
load_dotenv()

#from crews.support_crew import support_crew_fresh, support_crew_conversation
from crews.support_crew import support_crew_fresh_with_review

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "fresh"

    if mode == "conversation":
        crew = support_crew_conversation
        print("🔄 Responding to ongoing ticket thread...")
    else:
        crew = support_crew_fresh
        print("✉️ Responding to new support message...")

    result = crew.kickoff()
    print("\n=== Support Reply Suggestion ===\n")
    print(result)

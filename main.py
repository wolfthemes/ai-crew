from dotenv import load_dotenv
load_dotenv()

from crews.support_crew import support_crew

if __name__ == "__main__":
    result = support_crew.kickoff()
    print("\n=== Support Reply Suggestion ===\n")
    print(result)

# run_json_ticket.py
from utils.ticket_utils import preprocess_all_tickets, save_preprocessed_tickets
from utils.ticket_classifier import classify_ticket

# Theme metadata stub (replace with real dynamic loading later)
theme_metadata = {
    "Omnity": {"builder": "Elementor"},
    "MediaFoundry": {"builder": "Elementor"},
    "Gaintab": {"builder": "WPBakery"},
}

def main():

    try:
        print("📦 Preprocessing all open tickets...")

        tickets = preprocess_all_tickets(
            filepath="data/crawled/open_tickets.json",
            theme_metadata=theme_metadata,
            classify_ticket_func=classify_ticket,
        )

        save_preprocessed_tickets(tickets, output_path="data/dynamic/preprocessed_tickets.json")
        print(f"✅ {len(tickets)} tickets saved to preprocessed_tickets.json")

    except Exception as e:
        print(f"\n❌ Error running tickets preprocessor: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
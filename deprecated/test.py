import os
from datetime import datetime
from pprint import pformat
from crews.support_crew import support_crew_with_research

def log_crew_result_to_file(ticket_text: str, result: dict, log_dir: str = "logs") -> str:
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(log_dir, f"crew_result_{timestamp}.log")

    # Start composing log content
    log_lines = []

    log_lines.append("📩 ORIGINAL TICKET:\n")
    log_lines.append(ticket_text.strip())
    log_lines.append("\n" + "="*80 + "\n")

    for key in ["research", "reply", "review"]:
        task = result.get(key)
        log_lines.append(f"\n🧠 === {key.upper()} ===")

        if hasattr(task, "description"):
            log_lines.append("\n🔍 Task Description:\n" + task.description.strip())
        if hasattr(task, "output"):
            log_lines.append("\n📤 Output:\n" + getattr(task.output, "raw", str(task.output)).strip())
        elif isinstance(task, str):
            log_lines.append("\n📤 Output:\n" + task.strip())

        if hasattr(task, "metadata"):
            log_lines.append("\n🧾 Metadata:\n" + pformat(task.metadata))

        log_lines.append("\n" + "="*80 + "\n")

    # Write all content to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"📁 Full log written to: {filename}")
    return filename

ticket_text = """
Ticket from user:
"How to update WPBakery with Herion?
John"
"""

result = support_crew_with_research(ticket_text)
log_crew_result_to_file(ticket_text, result)
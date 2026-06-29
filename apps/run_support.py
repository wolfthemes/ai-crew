import subprocess
import webbrowser
import time
import os
import sys

# Define the apps to launch
apps = [
    {"script": "apps/fresh_ticket.py", "port": 8501, "name": "Fresh Ticket"},
    {"script": "apps/ticket_dashboard.py", "port": 8502, "name": "Ticket Dashboard"},
]

# Start all Streamlit apps
for app in apps:
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", app["script"],
        "--server.port", str(app["port"]),
        "--server.headless", "true"
    ])
    print(f"Started {app['name']} on port {app['port']}")
    time.sleep(2)

# Wait for apps to initialize
print("Waiting for apps to initialize...")
time.sleep(5)

# Open the main app in Brave
ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "support_dashboard_ui.html"))
webbrowser.register("brave", None, webbrowser.BackgroundBrowser("/mnt/c/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"))
webbrowser.get("brave").open(f"file://{ui_path}")

# Keep the script running
print("Press Ctrl+C to exit and terminate all apps")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    # You could add code here to terminate all the Streamlit processes
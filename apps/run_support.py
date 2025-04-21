import subprocess
import webbrowser
import time
import os

# Define the apps to launch
apps = [
    {"script": "apps/chat_dev_agent.py", "port": 8501, "name": "Dev Agent"},
    {"script": "apps/fresh_ticket.py", "port": 8502, "name": "Fresh Ticket"},
    {"script": "apps/ticket_dashboard.py", "port": 8503, "name": "Ticket Dashboard"},
]

# Start all Streamlit apps
for app in apps:
    subprocess.Popen([
        "streamlit", "run", app["script"],
        "--server.port", str(app["port"]),
        "--server.headless", "true"
    ])
    print(f"Started {app['name']} on port {app['port']}")
    time.sleep(2)

# Wait for apps to initialize
print("Waiting for apps to initialize...")
time.sleep(5)

# Open the main app in the default browser
webbrowser.open(f"http://localhost:{apps[2]['port']}")

# Keep the script running
print("Press Ctrl+C to exit and terminate all apps")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    # You could add code here to terminate all the Streamlit processes
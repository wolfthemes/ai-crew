import subprocess
import webview
import threading
import time

# Define your apps and ports
apps = [
    {"name": "Fresh Ticket", "script": "fresh_ticket.py", "port": 8501},
    {"name": "Ticket Dashboard", "script": "ticket_dashboard.py", "port": 8502},
    {"name": "Dev Agent", "script": "chat_dev_agent.py", "port": 8503},
]

processes = []

def run_streamlit(script, port):
    # Launch each Streamlit app on its port
    p = subprocess.Popen(["streamlit", "run", script, "--server.port", str(port)])
    processes.append(p)

def start_all_apps():
    for app in apps:
        threading.Thread(target=run_streamlit, args=(app["script"], app["port"]), daemon=True).start()
        time.sleep(1.5)  # Give each app time to start to avoid port conflicts

def open_webview():
    windows = [
        webview.create_window(app["name"], f"http://localhost:{app['port']}", width=1200, height=800)
        for app in apps
    ]
    webview.start(gui='edgechromium')  # Use qt or cef for better control

if __name__ == "__main__":
    start_all_apps()
    time.sleep(4)  # Wait a bit for servers to initialize
    open_webview()

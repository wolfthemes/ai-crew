import subprocess
import webview
import threading
import time

apps = [
    {"script": "apps/chat_dev_agent.py", "port": 8501},
    {"script": "apps/fresh_ticket.py", "port": 8502},
    {"script": "apps/ticket_dashboard.py", "port": 8503},
]    

def run_streamlit(script, port):
    subprocess.Popen([
        "streamlit", "run", script,
        "--server.port", str(port),
        "--server.headless", "true"
    ])

def start_all_apps():
    for app in apps:
        threading.Thread(target=run_streamlit, args=(app["script"], app["port"]), daemon=True).start()
        time.sleep(1.5)

if __name__ == "__main__":
    start_all_apps()
    time.sleep(4)
    webview.create_window("AI Crew Dashboard", "dashboard_ui.html", width=1280, height=800)
    webview.start(gui='edgechromium')


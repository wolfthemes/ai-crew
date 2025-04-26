import subprocess
import webview
import threading
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the apps to launch
apps = [
    {"script": "apps/chat_dev_agent.py", "port": 8501, "name": "Dev Agent"},
    {"script": "apps/fresh_ticket.py", "port": 8502, "name": "Fresh Ticket"},
    {"script": "apps/ticket_dashboard.py", "port": 8503, "name": "Ticket Dashboard"},
]    

def run_streamlit(script, port, name):
    """Run a Streamlit app as a subprocess"""
    try:
        logger.info(f"Starting {name} on port {port}")
        subprocess.Popen([
            "streamlit", "run", script,
            "--server.port", str(port),
            "--server.headless", "true"
        ])
        logger.info(f"Started {name}")
    except Exception as e:
        logger.error(f"Error starting {name}: {e}")

def start_streamlit_apps():
    """Start all Streamlit apps"""
    for app in apps:
        run_streamlit(app["script"], app["port"], app["name"])
        # Wait a bit between starting apps to avoid port conflicts
        time.sleep(2)
    
    # Give apps time to initialize
    logger.info("Waiting for apps to initialize...")
    time.sleep(5)
    logger.info("All apps should be running now")

if __name__ == "__main__":
    # Start Streamlit apps in separate processes (not threads)
    start_streamlit_apps()
    
    # Create webview window on the main thread
    logger.info("Creating webview window")
    webview.create_window("AI Crew Dashboard", "dashboard_ui.html", width=1280, height=800)
    logger.info("Starting webview")
    webview.start(gui='edgechromium')
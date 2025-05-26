import http.server
import socketserver
import subprocess
import threading
import time
import os

PORT = 8000
DASHBOARD_FILE = "apps/content_dashboard_ui.html"

# Define Streamlit apps to launch
apps = [
    {"script": "apps/content_dashboard.py", "port": 8504, "name": "Content Dashboard"}
]

def run_streamlit(script, port, name):
    """Run a Streamlit app as a subprocess"""
    try:
        print(f"Starting {name} on port {port}")
        subprocess.Popen([
            "streamlit", "run", script,
            "--server.port", str(port),
            "--server.headless", "true"
        ])
        print(f"Started {name}")
    except Exception as e:
        print(f"Error starting {name}: {e}")

def start_streamlit_apps():
    """Start all Streamlit apps"""
    for app in apps:
        run_streamlit(app["script"], app["port"], app["name"])
        time.sleep(2)  # Small delay between starting apps
    print("Waiting a few seconds for apps to initialize...")
    time.sleep(5)

def open_brave(url):
    try:
        brave_path = "/mnt/c/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
        if not os.path.exists(brave_path):
            brave_path = "/mnt/c/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"
        
        if not os.path.exists(brave_path):
            raise FileNotFoundError("Brave browser not found.")
        
        subprocess.Popen([
            brave_path,
            "--new-window",
            "--window-size=1280,800",
            #f"--app={url}",
            f"--app=http://localhost:8000/content_dashboard_ui.html",
            #"--window-position=100,100"
            #"--new-window",
            #url
        ])
    except Exception as e:
        print(f"Could not open Brave automatically: {e}")
        print(f"Please manually open: {url}")

def start_server():
    # Always serve files from the folder where support_dashboard_ui.html is
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Check that dashboard file exists
    if not os.path.exists(DASHBOARD_FILE):
        print(f"Error: {DASHBOARD_FILE} not found in current directory.")
        exit(1)
    
    # Start all Streamlit apps first
    start_streamlit_apps()
    
    # Start dashboard HTTP server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    time.sleep(1)
    
    # Open Brave to dashboard page
    dashboard_url = f"http://localhost:{PORT}/{DASHBOARD_FILE}"
    print(f"Opening {dashboard_url} in Brave...")
    open_brave(dashboard_url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

"""PyInstaller entry point for LoreKeeper.
Starts the local web server and opens the browser automatically.
"""
import os
import sys
import threading
import time
import webbrowser

# Ensure bundled resources are findable
if getattr(sys, '_MEIPASS', None):
    os.chdir(sys._MEIPASS)

def open_browser(port):
    """Wait for server to start, then open browser."""
    time.sleep(2)
    webbrowser.open(f"http://localhost:{port}")

def main():
    port = int(os.environ.get("GAMECOMPANION_PORT", "8000"))
    
    # Open browser in background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Import and start the app
    from gamecompanion.main import serve, PORT
    serve(port=port)

if __name__ == "__main__":
    main()

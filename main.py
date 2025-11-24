#!/usr/bin/env python3
"""
ESA Helper - Main Entry Point

Launches the Flask web application for automating ClassWallet submissions.

Usage:
    python main.py

This will start the Flask development server and open the application in your default browser (Chrome).
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app


def main():
    """Start the Flask application"""
    app = create_app()

    print("\n" + "=" * 60)
    print("ESA Helper - ClassWallet Automation Tool")
    print("=" * 60)
    print("\nStarting Flask application...")
    print("Open your browser and navigate to: http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop the server\n")

    # Only open browser on the main process (not the reloader subprocess)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Try to open in Chrome browser
        def open_chrome():
            try:
                # Give Flask a moment to start
                time.sleep(1)
                # Try to open with Chrome explicitly
                subprocess.Popen([
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    'http://127.0.0.1:5000'
                ])
            except Exception as e:
                print(f"Note: Could not auto-open Chrome. Open http://127.0.0.1:5000 manually in Chrome")

        # Start chrome opener in background
        import threading
        chrome_thread = threading.Thread(target=open_chrome, daemon=True)
        chrome_thread.start()

    # Start Flask development server
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)


if __name__ == '__main__':
    main()
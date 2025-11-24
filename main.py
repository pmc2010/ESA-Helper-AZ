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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system environment variables

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app


def main():
    """Start the Flask application"""
    app = create_app()

    # Get port from environment variable, default to 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')

    print("\n" + "=" * 60)
    print("ESA Helper - ClassWallet Automation Tool")
    print("=" * 60)
    print("\nStarting Flask application...")
    print(f"Open your browser and navigate to: http://{host}:{port}")
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
                    f'http://{host}:{port}'
                ])
            except Exception as e:
                print(f"Note: Could not auto-open Chrome. Open http://{host}:{port} manually in Chrome")

        # Start chrome opener in background
        import threading
        chrome_thread = threading.Thread(target=open_chrome, daemon=True)
        chrome_thread.start()

    # Start Flask development server
    app.run(debug=True, host=host, port=port, use_reloader=True)


if __name__ == '__main__':
    main()
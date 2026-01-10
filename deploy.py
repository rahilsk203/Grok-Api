#!/usr/bin/env python3
"""
Deployment script for Grok API
This script starts the Flask server with optimal settings for production use
"""

import os
import sys
from api_server import app

def main():
    """
    Main function to start the Grok API server
    """
    print("Starting Grok API Server...")
    print("================================")
    print(f"Server will run on http://0.0.0.0:6969")
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Run the Flask app with production-ready settings
        app.run(
            host="0.0.0.0",      # Bind to all interfaces
            port=6969,           # Default port
            debug=False,         # Disable debug in production
            threaded=True,       # Enable threading for concurrent requests
            use_reloader=False   # Disable reloader in production
        )
    except KeyboardInterrupt:
        print("\nShutting down Grok API Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import time

os.chdir('frontend')
PORT = 3000

Handler = http.server.SimpleHTTPRequestHandler
print(f"🚀 Starting frontend server on http://localhost:{PORT}")
print("📱 Opening browser automatically...")

# Start server in background
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"✅ Frontend server running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    # Open browser after a short delay
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down frontend server...")
        httpd.shutdown()
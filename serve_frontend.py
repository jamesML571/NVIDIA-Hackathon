#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend
Avoids CORS issues with file:// protocol
"""
import http.server
import socketserver
import os
import sys

# Change to frontend directory
os.chdir('frontend')

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Custom logging
        print(f"[Frontend] {format % args}")

Handler = MyHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 60)
        print("Frontend Server Started")
        print("=" * 60)
        print(f"\nFrontend URL: http://localhost:{PORT}")
        print(f"Backend API: http://localhost:8000")
        print(f"\nOpen http://localhost:{PORT} in your browser")
        print("\nPress Ctrl+C to stop the server\n")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n\nShutting down frontend server...")
    sys.exit(0)
except OSError as e:
    if e.errno == 10048:  # Port already in use on Windows
        print(f"\n❌ Error: Port {PORT} is already in use")
        print("Try closing other applications or use a different port")
    else:
        print(f"\n❌ Error: {e}")
    sys.exit(1)

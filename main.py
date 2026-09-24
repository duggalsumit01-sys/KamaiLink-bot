import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Render Port Error Fix
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Start Web Server in Background
threading.Thread(target=run_dummy_server, daemon=True).start()

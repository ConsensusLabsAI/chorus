"""
Simple web server for Chorus prompt versioning tool.
"""

import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import threading
import time

from .core import PromptStorage
from .utils.colors import Colors


class ChorusHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Simple HTTP handler for the web interface."""
    
    def __init__(self, *args, **kwargs):
        web_path = Path(__file__).parent / "web"
        super().__init__(*args, directory=str(web_path), **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/prompts':
            self.handle_api_prompts()
        elif parsed_path.path in ['/', '/index.html']:
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()
    
    def handle_api_prompts(self):
        """Handle /api/prompts endpoint."""
        try:
            storage = PromptStorage()
            prompts = storage.list_prompts()
            
            # Convert to dictionary format
            prompts_data = {}
            for prompt in prompts:
                key = f"{prompt.function_name}_{prompt.version}"
                prompts_data[key] = prompt.to_dict()
            
            self.send_json_response(prompts_data)
        except Exception as e:
            self.send_error(500, f"Error loading prompts: {str(e)}")
    
    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def start_web_server(port=3000, open_browser=True):
    """Start the web server."""
    web_path = Path(__file__).parent / "web"
    index_file = web_path / "index.html"
    
    if not index_file.exists():
        print(f"{Colors.RED}Web interface not found at {web_path}{Colors.END}")
        return
    
    # Find available port
    for test_port in range(port, port + 10):
        try:
            server_address = ('', test_port)
            httpd = HTTPServer(server_address, ChorusHTTPRequestHandler)
            break
        except OSError:
            continue
    else:
        print(f"{Colors.RED}Could not find an available port{Colors.END}")
        return
    
    if test_port != port:
        print(f"{Colors.YELLOW}Port {port} in use, using port {test_port}{Colors.END}")
    
    print(f"{Colors.GREEN}{Colors.BOLD}Chorus web server: http://localhost:{test_port}{Colors.END}")
    print(f"{Colors.CYAN}Press Ctrl+C to stop{Colors.END}")
    
    # Open browser
    if open_browser:
        def open_browser_delayed():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{test_port}')
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.END}")
        httpd.shutdown()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start Chorus web server")
    parser.add_argument("--port", type=int, default=3000, help="Port to run server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()
    start_web_server(port=args.port, open_browser=not args.no_browser)
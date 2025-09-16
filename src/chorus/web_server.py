"""
Web server for Chorus prompt versioning tool.
Serves the React client and provides API endpoints for prompt data.
"""

import json
import os
import socket
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any
import threading
import time

from .core import PromptStorage


# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class ChorusHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler that serves the React app and provides API endpoints."""
    
    def __init__(self, *args, **kwargs):
        # Set the document root to the client build directory
        self.client_path = Path(__file__).parent.parent.parent / "src" / "client"
        self.dist_path = self.client_path / "dist"
        super().__init__(*args, directory=str(self.dist_path), **kwargs)
    
    def do_GET(self):
        """Handle GET requests for both static files and API endpoints."""
        parsed_path = urlparse(self.path)
        
        # API endpoints
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
        else:
            # Check if it's a static asset (JS, CSS, images, etc.)
            if (parsed_path.path.startswith('/assets/') or 
                parsed_path.path.endswith('.js') or 
                parsed_path.path.endswith('.css') or 
                parsed_path.path.endswith('.svg') or
                parsed_path.path.endswith('.ico')):
                # Serve static files normally
                super().do_GET()
            else:
                # Serve React app for all other routes (SPA routing)
                self.path = '/index.html'
                super().do_GET()
    
    def handle_api_request(self, parsed_path):
        """Handle API requests for prompt data."""
        try:
            if parsed_path.path == '/api/prompts':
                self.get_prompts()
            elif parsed_path.path == '/api/prompts/stats':
                self.get_prompts_stats()
            else:
                self.send_error(404, "API endpoint not found")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def get_prompts(self):
        """Get all prompts from storage."""
        try:
            storage = PromptStorage()
            prompts = storage.list_prompts()
            
            # Convert to dictionary format for JSON response
            prompts_data = {}
            for prompt in prompts:
                key = f"{prompt.function_name}_{prompt.version}"
                prompts_data[key] = prompt.to_dict()
            
            self.send_json_response(prompts_data)
        except Exception as e:
            self.send_error(500, f"Error loading prompts: {str(e)}")
    
    def get_prompts_stats(self):
        """Get statistics about stored prompts."""
        try:
            storage = PromptStorage()
            all_prompts = storage.list_prompts()
            
            # Group by function name
            by_function = {}
            for prompt in all_prompts:
                func_name = prompt.function_name
                if func_name not in by_function:
                    by_function[func_name] = []
                by_function[func_name].append(prompt)
            
            stats = {
                'total_prompts': len(all_prompts),
                'total_functions': len(by_function),
                'functions': {
                    func_name: {
                        'count': len(prompts),
                        'latest_version': max(prompts, key=lambda x: x.version).version,
                        'tags': list(set(tag for p in prompts for tag in p.tags))
                    }
                    for func_name, prompts in by_function.items()
                }
            }
            
            self.send_json_response(stats)
        except Exception as e:
            self.send_error(500, f"Error loading stats: {str(e)}")
    
    def send_json_response(self, data: Dict[str, Any]):
        """Send JSON response with proper headers."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


def find_available_port(start_port: int = 3000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")


def start_web_server(port: int = 3000, open_browser: bool = True):
    """Start the web server and optionally open the browser."""
    # Check if client is built
    client_path = Path(__file__).parent.parent.parent / "src" / "client"
    build_path = client_path / "dist"
    
    if not build_path.exists():
        print(f"{Colors.RED}Client not built. Building React app...{Colors.END}")
        build_react_app(client_path)
    
    # Find available port
    try:
        actual_port = find_available_port(port)
        if actual_port != port:
            print(f"{Colors.YELLOW}Warning: Port {port} is in use, using port {actual_port} instead{Colors.END}")
    except RuntimeError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return
    
    # Start server
    server_address = ('', actual_port)
    httpd = HTTPServer(server_address, ChorusHTTPRequestHandler)
    
    print(f"{Colors.GREEN}{Colors.BOLD}Chorus web server starting on http://localhost:{actual_port}{Colors.END}")
    print(f"{Colors.CYAN}Serving from: {client_path}{Colors.END}")
    print(f"{Colors.WHITE}Press Ctrl+C to stop the server{Colors.END}")
    
    # Open browser in a separate thread
    if open_browser:
        def open_browser_delayed():
            time.sleep(1)  # Give server time to start
            webbrowser.open(f'http://localhost:{actual_port}')
        
        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down server...{Colors.END}")
        httpd.shutdown()


def build_react_app(client_path: Path):
    """Build the React app for production."""
    import subprocess
    import sys
    
    try:
        print(f"{Colors.BLUE}Installing dependencies...{Colors.END}")
        subprocess.run([sys.executable, "-m", "npm", "install"], 
                      cwd=client_path, check=True, capture_output=True)
        
        print(f"{Colors.BLUE}Building React app...{Colors.END}")
        subprocess.run([sys.executable, "-m", "npm", "run", "build"], 
                      cwd=client_path, check=True, capture_output=True)
        
        print(f"{Colors.GREEN}React app built successfully!{Colors.END}")
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error building React app: {e}{Colors.END}")
        print(f"{Colors.YELLOW}Make sure Node.js and npm are installed{Colors.END}")
        raise
    except FileNotFoundError:
        print(f"{Colors.RED}npm not found. Please install Node.js and npm{Colors.END}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Chorus web server")
    parser.add_argument("--port", type=int, default=3000, help="Port to run server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    start_web_server(port=args.port, open_browser=not args.no_browser)

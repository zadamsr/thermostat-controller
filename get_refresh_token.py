#!/usr/bin/env python3
"""
Resideo OAuth 2.0 Authorization Script
This script helps you obtain a refresh token for the Resideo API.
"""

import requests
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import base64
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

CLIENT_ID = os.getenv("RESIDEO_CLIENT_ID")
CLIENT_SECRET = os.getenv("RESIDEO_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"
BASE_URL = "https://api.honeywellhome.com"

# Store the authorization code
auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback from Resideo."""

    def do_GET(self):
        global auth_code

        # Parse the callback URL
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>No authorization code received.</p>
                </body>
                </html>
            """)

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def get_authorization_url():
    """Generate the OAuth authorization URL."""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI
    }
    return f"{BASE_URL}/oauth2/authorize?{urlencode(params)}"


def exchange_code_for_token(code):
    """Exchange authorization code for access and refresh tokens."""
    url = f"{BASE_URL}/oauth2/token"

    # Resideo requires Basic Auth with client credentials
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded}"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def update_env_file(refresh_token):
    """Update the .env file with the new refresh token."""
    env_path = ".env"

    # Read existing .env content
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update the refresh token line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("RESIDEO_REFRESH_TOKEN="):
            lines[i] = f"RESIDEO_REFRESH_TOKEN={refresh_token}\n"
            updated = True
            break

    # If not found, append it
    if not updated:
        lines.append(f"RESIDEO_REFRESH_TOKEN={refresh_token}\n")

    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(lines)


def main():
    print("=" * 60)
    print("Resideo OAuth 2.0 Authorization")
    print("=" * 60)
    print()

    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: Missing CLIENT_ID or CLIENT_SECRET in .env file")
        return

    # Step 1: Get authorization URL
    auth_url = get_authorization_url()
    print("Step 1: Opening browser for authorization...")
    print(f"URL: {auth_url}")
    print()
    print("If the browser doesn't open automatically, copy this URL:")
    print(auth_url)
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Step 2: Start local server to capture callback
    print("Step 2: Waiting for authorization callback...")
    print("(A local server is running on port 8080)")
    print()

    server = HTTPServer(('localhost', 8080), CallbackHandler)
    server.handle_request()  # Handle one request (the callback)

    if not auth_code:
        print("ERROR: No authorization code received")
        return

    print(f"Authorization code received: {auth_code[:20]}...")
    print()

    # Step 3: Exchange code for tokens
    print("Step 3: Exchanging authorization code for tokens...")
    try:
        token_response = exchange_code_for_token(auth_code)

        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")

        print("SUCCESS! Tokens received:")
        print(f"  Access Token: {access_token[:30]}...")
        print(f"  Refresh Token: {refresh_token}")
        print(f"  Expires In: {expires_in} seconds")
        print()

        # Step 4: Save refresh token to .env
        print("Step 4: Saving refresh token to .env file...")
        update_env_file(refresh_token)
        print("Refresh token saved!")
        print()
        print("=" * 60)
        print("Setup complete! You can now use thermostat.py")
        print("=" * 60)

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Failed to exchange code for token")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()

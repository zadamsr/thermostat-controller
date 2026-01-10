#!/usr/bin/env python3
"""Debug script to test token refresh"""

import requests
import os
from dotenv import load_dotenv
import base64

load_dotenv()

CLIENT_ID = os.getenv("RESIDEO_CLIENT_ID")
CLIENT_SECRET = os.getenv("RESIDEO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("RESIDEO_REFRESH_TOKEN")
BASE_URL = "https://api.honeywellhome.com"

print("Credentials loaded:")
print(f"CLIENT_ID: {CLIENT_ID}")
print(f"CLIENT_SECRET: {CLIENT_SECRET}")
print(f"REFRESH_TOKEN: {REFRESH_TOKEN}")
print()

# Try Method 1: Credentials in body (current method)
print("=" * 60)
print("Method 1: Credentials in request body")
print("=" * 60)
url = f"{BASE_URL}/oauth2/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "grant_type": "refresh_token",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN
}

response = requests.post(url, headers=headers, data=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
print()

# Try Method 2: Basic Auth header
print("=" * 60)
print("Method 2: Basic Auth header + refresh_token in body")
print("=" * 60)
credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
encoded = base64.b64encode(credentials.encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {encoded}"
}
data = {
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN
}

response = requests.post(url, headers=headers, data=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

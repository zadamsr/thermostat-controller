#!/usr/bin/env python3
"""Check device capabilities and current settings"""

import requests
import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("RESIDEO_CLIENT_ID")
CLIENT_SECRET = os.getenv("RESIDEO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("RESIDEO_REFRESH_TOKEN")
BASE_URL = "https://api.honeywellhome.com"

def get_access_token():
    """Get a fresh access token"""
    url = f"{BASE_URL}/oauth2/token"
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
    response.raise_for_status()
    return response.json()["access_token"]

# Get device info
access_token = get_access_token()
params = {"apikey": CLIENT_ID}
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/v2/locations", headers=headers, params=params)
data = response.json()

print("Full device data:")
print(json.dumps(data[0]["devices"][0], indent=2))

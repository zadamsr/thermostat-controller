#!/usr/bin/env python3
"""Test different HTTP methods for setting temperature"""

import requests
import os
import base64
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

# Get device ID
access_token = get_access_token()
print(f"Access token: {access_token}\n")

# Get device info
params = {"apikey": CLIENT_ID}
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/v2/locations", headers=headers, params=params)
data = response.json()
device_id = data[0]["devices"][0]["deviceID"]
print(f"Device ID: {device_id}\n")

# Test payloads
payloads = [
    {"mode": "Heat", "heatSetpoint": 70},
    {"heatSetpoint": 70},
    {"mode": "Heat", "heatSetpoint": 70, "autoChangeoverActive": False},
]

methods = ["POST", "PUT", "PATCH"]

for method in methods:
    for i, payload in enumerate(payloads):
        print("=" * 60)
        print(f"Testing {method} with payload #{i+1}: {payload}")
        print("=" * 60)

        url = f"{BASE_URL}/v2/devices/thermostats/{device_id}?apikey={CLIENT_ID}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        if method == "POST":
            response = requests.post(url, headers=headers, json=payload)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=payload)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=payload)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()

        if response.ok:
            print("SUCCESS!")
            break
    else:
        continue
    break

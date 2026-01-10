#!/usr/bin/env python3
"""Test with PUT method on location-based endpoints"""

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

# Get location and device info
access_token = get_access_token()
params = {"apikey": CLIENT_ID}
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/v2/locations", headers=headers, params=params)
data = response.json()

location_id = data[0]["locationID"]
device_id = data[0]["devices"][0]["deviceID"]

print(f"Location ID: {location_id}")
print(f"Device ID: {device_id}\n")

# Test with PUT
endpoint = f"/v2/devices/thermostats/{device_id}"
payload = {"mode": "Heat", "heatSetpoint": 70}

print("=" * 60)
print(f"Testing PUT on: {endpoint}")
print(f"Payload: {payload}")
print("=" * 60)

url = f"{BASE_URL}{endpoint}?apikey={CLIENT_ID}"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.put(url, headers=headers, json=payload)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.ok:
    print("\nSUCCESS!")

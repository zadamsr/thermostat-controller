"""
Resideo Thermostat API Module
Handles authentication and temperature control for Honeywell Home thermostats
"""

import requests
import time
import os
import base64
from dotenv import load_dotenv

# Load credentials
load_dotenv()

CLIENT_ID = os.getenv("RESIDEO_CLIENT_ID")
CLIENT_SECRET = os.getenv("RESIDEO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("RESIDEO_REFRESH_TOKEN")

# Validate credentials
if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
    raise RuntimeError("Missing Resideo credentials in .env file")

ACCESS_TOKEN = None
TOKEN_EXPIRES_AT = 0
BASE_URL = "https://api.honeywellhome.com"


def refresh_access_token():
    """Refresh the access token using the refresh token."""
    global ACCESS_TOKEN, TOKEN_EXPIRES_AT

    url = f"{BASE_URL}/oauth2/token"

    # Resideo requires Basic Auth with client credentials
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
    resp_json = response.json()

    ACCESS_TOKEN = resp_json["access_token"]
    expires_in = int(resp_json.get("expires_in", 3600))
    TOKEN_EXPIRES_AT = time.time() + expires_in

    return ACCESS_TOKEN


def get_valid_access_token():
    """Return a valid access token, refreshing if expired or near expiry."""
    global ACCESS_TOKEN, TOKEN_EXPIRES_AT
    if ACCESS_TOKEN is None or time.time() >= TOKEN_EXPIRES_AT - 30:
        refresh_access_token()
    return ACCESS_TOKEN


def api_get(path, params=None):
    """GET request with automatic access token AND apikey parameter."""
    if params is None:
        params = {}

    # Resideo requires the Consumer Key in the URL parameters
    params["apikey"] = CLIENT_ID

    headers = {"Authorization": f"Bearer {get_valid_access_token()}"}
    r = requests.get(f"{BASE_URL}{path}", headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def api_post(path, payload, location_id=None):
    """POST request with apikey and locationId parameters."""
    # Resideo requires both apikey and locationId parameters
    url = f"{BASE_URL}{path}?apikey={CLIENT_ID}"
    if location_id:
        url += f"&locationId={location_id}"

    headers = {
        "Authorization": f"Bearer {get_valid_access_token()}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    return r.json() if r.text else None


def get_location_id():
    """Get the first location ID for this account."""
    data = api_get("/v2/locations")
    if not data:
        raise RuntimeError("No locations found")
    return data[0]["locationID"]


def get_thermostat_status():
    """Get current thermostat status including temperature and setpoints."""
    data = api_get("/v2/locations")
    if not data or not data[0].get("devices"):
        raise RuntimeError("No thermostat found")

    location_id = data[0]["locationID"]
    device = data[0]["devices"][0]
    changeable = device.get("changeableValues", {})

    return {
        "location_id": location_id,
        "device_id": device["deviceID"],
        "indoor_temperature": device["indoorTemperature"],
        "outdoor_temperature": device.get("outdoorTemperature"),
        "mode": changeable.get("mode"),
        "heat_setpoint": changeable.get("heatSetpoint"),
        "cool_setpoint": changeable.get("coolSetpoint"),
        "min_heat": device.get("minHeatSetpoint", 50),
        "max_heat": device.get("maxHeatSetpoint", 76),
        "min_cool": device.get("minCoolSetpoint", 67),
        "max_cool": device.get("maxCoolSetpoint", 90),
    }


def set_temperature(device_id, location_id, mode, heat_setpoint, cool_setpoint):
    """
    Set thermostat temperature.

    Args:
        device_id: Device ID
        location_id: Location ID
        mode: "Heat", "Cool", or "Auto"
        heat_setpoint: Heat temperature (required even in Cool mode)
        cool_setpoint: Cool temperature (required even in Heat mode)
    """
    payload = {
        "mode": mode,
        "heatSetpoint": int(heat_setpoint),
        "coolSetpoint": int(cool_setpoint),
        "thermostatSetpointStatus": "PermanentHold"
    }

    api_post(f"/v2/devices/thermostats/{device_id}", payload, location_id)

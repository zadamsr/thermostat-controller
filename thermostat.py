import requests
import sys
import time
import os
import base64
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

CLIENT_ID = os.getenv("RESIDEO_CLIENT_ID")
CLIENT_SECRET = os.getenv("RESIDEO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("RESIDEO_REFRESH_TOKEN")

# Validate that credentials are loaded
if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Missing credentials in .env file")
    print("Please ensure RESIDEO_CLIENT_ID and RESIDEO_CLIENT_SECRET are set")
    sys.exit(1)

if not REFRESH_TOKEN:
    print("ERROR: Missing RESIDEO_REFRESH_TOKEN in .env file")
    print("Please run 'python get_refresh_token.py' first to obtain a refresh token")
    sys.exit(1)

ACCESS_TOKEN = None
TOKEN_EXPIRES_AT = 0  # epoch time when token expires
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

    print("✅ Access token refreshed:", ACCESS_TOKEN)
    print("⏱ Expires in seconds:", expires_in)
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
    """POST request with apikey parameter."""
    # Resideo requires both apikey and locationId parameters
    url = f"{BASE_URL}{path}?apikey={CLIENT_ID}"
    if location_id:
        url += f"&locationId={location_id}"

    headers = {
        "Authorization": f"Bearer {get_valid_access_token()}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json=payload)

    if not r.ok:
        print(f"ERROR: API returned {r.status_code}")
        print(f"Response: {r.text}")

    r.raise_for_status()
    return r.json() if r.text else None


def get_location_id():
    """Get the first location ID for this account."""
    data = api_get("/v2/locations")
    if not data:
        raise RuntimeError("No locations found")
    return data[0]["locationID"]


def get_thermostat(location_id):
    """Get the first thermostat for a location."""
    data = api_get("/v2/locations")
    location = next((loc for loc in data if loc["locationID"] == location_id), None)
    if not location:
        raise RuntimeError("Location not found")
    devices = location.get("devices", [])
    if not devices:
        raise RuntimeError("No devices found")
    device = devices[0]
    device.update(device.get("changeableValues", {}))
    return device


def set_temperature(device_id, location_id, current_heat, current_cool, mode, heat=None, cool=None):
    """Set thermostat temperature with PermanentHold."""
    # Resideo requires both heatSetpoint and coolSetpoint in all modes
    payload = {
        "mode": mode,
        "thermostatSetpointStatus": "PermanentHold"
    }

    if mode == "Heat" and heat is not None:
        payload["heatSetpoint"] = int(heat)
        payload["coolSetpoint"] = int(current_cool)  # Keep current cool setpoint
    elif mode == "Cool" and cool is not None:
        payload["heatSetpoint"] = int(current_heat)  # Keep current heat setpoint
        payload["coolSetpoint"] = int(cool)
    elif mode == "Auto" and heat is not None and cool is not None:
        payload["heatSetpoint"] = int(heat)
        payload["coolSetpoint"] = int(cool)

    print("DEBUG: payload being sent:", payload)
    api_post(f"/v2/devices/thermostats/{device_id}", payload, location_id)


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Heat: python thermostat.py Heat 70")
        print("  Cool: python thermostat.py Cool 74")
        print("  Auto: python thermostat.py Auto 68 75")
        sys.exit(1)

    mode = sys.argv[1]
    heat = cool = None
    if mode == "Heat":
        heat = sys.argv[2]
    elif mode == "Cool":
        cool = sys.argv[2]
    elif mode == "Auto":
        heat = sys.argv[2]
        cool = sys.argv[3]
    else:
        raise ValueError("Mode must be Heat, Cool, or Auto")

    print("Locating thermostat...")
    location_id = get_location_id()
    thermostat = get_thermostat(location_id)
    device_id = thermostat["deviceID"]

    current_heat = thermostat.get("heatSetpoint")
    current_cool = thermostat.get("coolSetpoint")

    print("Current state:")
    print("  Indoor temp:", thermostat["indoorTemperature"])
    print("  Heat setpoint:", current_heat)
    print("  Cool setpoint:", current_cool)
    print("  Mode:", thermostat.get("mode"))

    print("\nSetting temperature...")
    set_temperature(device_id, location_id, current_heat, current_cool, mode, heat, cool)

    print("✅ Temperature command sent")
    print("⏳ It may take 10–30 seconds to reflect in the app")


if __name__ == "__main__":
    main()